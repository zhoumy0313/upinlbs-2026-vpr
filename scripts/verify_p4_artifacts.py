#!/usr/bin/env python3
"""Independent final-record replay. Never fits or calibrates on final data."""
import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from scipy.special import expit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from frozen_package import digest,validate_package


def read(path):
    return json.loads(path.read_text())


def independent_policy(spec,x):
    kind=spec['kind']
    if kind=='always_A':score=np.full(len(x),-1.)
    elif kind=='always_B':score=np.full(len(x),1.)
    elif kind=='gap':score=-x[:,1]
    elif kind=='random':score=np.random.default_rng(spec['seed']).random(len(x))
    else:
        heads=[]
        for h in spec['heads']:
            assert h['n_train']==600
            values=(x[:,h['columns']]-np.array(h['mean']))/np.array(h['scale'])
            heads.append(expit(values@np.array(h['coef'])+h['intercept']))
        score=heads[0]-heads[1] if kind in {'net_benefit','error_two_head','net_benefit_no_std'} else heads[0]
    t=spec['threshold']
    threshold={'always':-np.inf,'never':np.inf}.get(t['kind'],t['value'])
    return score,score>threshold


def same(value,expected):
    if expected is None:assert value is None
    else:np.testing.assert_allclose(value,expected,atol=1e-12,rtol=1e-12)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--acceptance-output',default='phase_acceptance.json',help='New JSON basename within the run; never overwrite an existing audit')
    args=parser.parse_args()
    package=validate_package(args.package)
    results=args.run_dir/'results'
    assert read(results/'completed.json')['final_evaluation_complete']
    identity=read(results/'freeze_identity.json')
    assert identity['package_sha256']==digest(args.package)
    assert identity['confirmation']==read(args.package.parent/'human_confirmation.json')
    events=[json.loads(line) for line in (args.run_dir/'commands.jsonl').read_text().splitlines()]
    final_events=[e for e in events if e['name']=='final_evaluation']
    assert len(final_events)==1 and final_events[0]['exit_status']==0
    # Renderer failures belong to their own append-only history, not the
    # validity of final inference. The required inference must have succeeded.
    checked={'offline_rows':0,'online_rows':0,'policy_radius_evaluations':0}
    sources={};outcomes={}
    for dataset,config in package['evaluation_plan']['datasets'].items():
        folder=results/dataset
        assert read(folder/'completed.json')['queries']==config['queries']
        manifest=args.package.parent/package['files'][dataset+'_manifest']['path']
        records=read(manifest)['records'];lookup={r['image_id']:r for r in records}
        role=config['query_role'];descriptors={};ids={};scores={};ranks={}
        for method in ['cosplace','dinov2','eigenplaces']:
            fp=read(folder/method/'fingerprint.json')
            assert fp['manifest_sha256']==digest(manifest)
            assert fp['model']['model_state_sha256']==package['model_state_sha256'][method]
            arrays={};ids[method]={}
            for split in ['gallery',role]:
                path=folder/method/(split+'_descriptors.npy')
                arrays[split]=np.load(path,allow_pickle=False)
                ids[method][split]=read(folder/method/(split+'_image_ids.json'))
                expected=[r['image_id'] for r in records if r['split']==split]
                assert ids[method][split]==expected
                entry=fp['roles'][split]
                assert digest(path)==entry['sha256'] and arrays[split].shape==tuple(entry['shape'])
                assert arrays[split].dtype==np.float32 and np.isfinite(arrays[split]).all()
                assert len(expected)==(config['gallery'] if split=='gallery' else config['queries'])
                np.testing.assert_allclose(np.linalg.norm(arrays[split],axis=1),1,atol=1e-5)
                sources[str(path.relative_to(args.run_dir))]=digest(path)
            descriptors[method]=arrays
            q=arrays[role].astype(np.float64);d=arrays['gallery'].astype(np.float64)
            q/=np.linalg.norm(q,axis=1,keepdims=True);d/=np.linalg.norm(d,axis=1,keepdims=True)
            scores[method]=np.clip(q@d.T,-1,1)
            ranks[method]=np.argsort(-scores[method],axis=1,kind='stable')[:,:10]
        qids=ids['cosplace'][role];dids=ids['cosplace']['gallery']
        assert all(ids[m][role]==qids and ids[m]['gallery']==dids for m in ids)
        qframes=np.array([lookup[i]['frame_index'] for i in qids]);dframes=np.array([lookup[i]['frame_index'] for i in dids])
        top=np.take_along_axis(scores['cosplace'],ranks['cosplace'],axis=1)
        x=np.column_stack([top[:,0],top[:,0]-top[:,1],top[:,0]-top[:,4],top.mean(axis=1),top.std(axis=1)])
        for second in ['eigenplaces','dinov2']:
            pair=folder/('pair_'+second)
            policies=read(args.package.parent/package['files'][second+'_policies']['path'])['policies']
            assert len(policies)==50
            masks={n:independent_policy(s,x) for n,s in policies.items()}
            accuracy=read(pair/'accuracy.json');assert accuracy['threshold_recalibrated'] is False
            offline=list(csv.DictReader((pair/'accuracy_per_query.csv').open()))
            assert len(offline)==50*config['queries'];checked['offline_rows']+=len(offline)
            for radius in [config['primary_radius']]+config['sensitivity_radii']:
                good={m:np.abs(dframes[ranks[m]]-qframes[:,None])<=radius for m in ['cosplace',second]}
                a=good['cosplace'][:,0];b=good[second][:,0]
                if radius==config['primary_radius']:
                    outcomes[dataset+'_'+second]={'both_right':int((a&b).sum()),'rescue':int((~a&b).sum()),
                        'harm':int((a&~b).sum()),'both_wrong':int((~a&~b).sum())}
                primary=accuracy['by_radius'][str(radius)]
                assert len(primary)==51
                replay={**masks,'oracle_DIAGNOSTIC_ONLY':(None,(~a)&b)}
                for name,(score,mask) in replay.items():
                    metric=primary[name];hits=np.where(mask[:,None],good[second],good['cosplace'])
                    rescue=int((mask&~a&b).sum());harm=int((mask&a&~b).sum());invoked=int(mask.sum())
                    expected={'n_queries':len(qids),'n_invoked':invoked,'invocation_fraction':mask.mean(),'rescues':rescue,'harms':harm,
                        'net_gain_percentage_points':100*(rescue-harm)/len(qids),'fast_r1':a.mean(),'second_r1':b.mean(),
                        'routed_r1':hits[:,0].mean(),'oracle_r1_DIAGNOSTIC_ONLY':(a|b).mean(),
                        'rescue_fraction_among_invoked':rescue/invoked if invoked else None,
                        'harm_fraction_among_invoked':harm/invoked if invoked else None,
                        **{f'R@{k}':hits[:,:k].any(axis=1).mean() for k in [1,5,10]}}
                    for key,value in expected.items():same(metric[key],value)
                    checked['policy_radius_evaluations']+=1
                    if radius==config['primary_radius'] and score is not None:
                        rows=[r for r in offline if r['policy']==name]
                        assert [r['query_image_id'] for r in rows]==qids
                        np.testing.assert_allclose([float(r['gate_score']) for r in rows],score,atol=1e-12,rtol=1e-12)
                        np.testing.assert_array_equal([r['invoked_B']=='True' for r in rows],mask)
                        for i,row in enumerate(rows):
                            assert (row['A_correct']=='True')==bool(a[i]) and (row['B_correct']=='True')==bool(b[i])
                            assert (row['routed_correct']=='True')==bool(hits[i,0])
                            chosen=second if mask[i] else 'cosplace'
                            assert json.loads(row['top10_image_ids'])==[dids[j] for j in ranks[chosen][i]]
            primary=accuracy['by_radius'][str(config['primary_radius'])]
            for prefix,summary in accuracy['random_all_seeds'].items():
                values=[primary[prefix+f'_seed{s}'] for s in range(5)]
                for key,value in summary.items():
                    same(value['mean'],np.mean([v[key] for v in values]));same(value['std_population'],np.std([v[key] for v in values]))
            latency=read(pair/'latency.json')
            assert latency['real_forwards'] and not latency['cached_query_inside_timer']
            assert latency['batch_size']==1 and latency['warmup_per_policy']==20 and latency['full_passes']==3
            assert len(latency['policies'])==21
            for name,metric in latency['policies'].items():
                path=pair/(name+'_latency.csv');rows=list(csv.DictReader(path.open()))
                assert len(rows)==3*len(qids)==metric['n_queries'];checked['online_rows']+=len(rows)
                assert metric['real_rankings_and_masks_match_cached_reference']
                assert metric['A_forward_calls']==(0 if name=='B_only' else len(rows))
                assert metric['B_forward_calls']==sum(r['invoked_B']=='True' for r in rows)
                times=np.array([float(r['total_ms']) for r in rows])
                assert np.isfinite(times).all() and (times>0).all()
                for key,value in [('mean_ms',times.mean()),('median_ms',np.median(times)),('p95_ms',np.percentile(times,95))]:same(metric[key],value)
                same(metric['invocation_fraction'],primary[name]['invocation_fraction'])
                for repeat in range(3):
                    subset=[r for r in rows if int(r['pass'])==repeat]
                    assert [r['query_image_id'] for r in subset]==qids
                    np.testing.assert_array_equal([r['invoked_B']=='True' for r in subset],masks[name][1])
                    for i,row in enumerate(subset):
                        chosen=second if masks[name][1][i] else 'cosplace'
                        assert row['top1_image_id']==dids[ranks[chosen][i,0]]
                sources[str(path.relative_to(args.run_dir))]=digest(path)
            for file in ['accuracy.json','accuracy_per_query.csv','latency.json']:
                sources[str((pair/file).relative_to(args.run_dir))]=digest(pair/file)
    result={'passed':True,'scope':'Both final datasets and model pairs; all frozen policies, tolerances and real measured passes',
        **checked,'outcomes':outcomes,'no_refitting_or_threshold_calibration':True,'package_sha256':digest(args.package),
        'verifier_sha256':digest(Path(__file__)),'source_sha256':sources}
    assert Path(args.acceptance_output).name==args.acceptance_output
    with (args.run_dir/args.acceptance_output).open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()
