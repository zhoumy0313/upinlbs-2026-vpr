"""Bounded predeclared development search; no independent or old-test scores."""
import csv
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import index_positives
from causal import cosine_unit_scores,rrf,stream_scores,stable_ranking,fixed_affine,blend_scores
from diagnostics import canonical_rows
from runtime import Run,digest,update_state

def metrics_for(scores,positive,mask):
    ranks=stable_ranking(scores,10)
    hit=np.take_along_axis(positive,ranks,axis=1)
    return ranks,{f'R@{k}':dict(correct=int(hit[mask,:k].any(axis=1).sum()),queries=int(mask.sum()),
        recall=float(hit[mask,:k].any(axis=1).mean())) for k in [1,5,10]}

def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text())
    predecl=ROOT/state['g2_search_predeclaration']
    plan=json.loads(predecl.read_text())['next_grid']
    manifest=ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json'
    dino=ROOT/'outputs_v2'/state['g1_diagnosis_run']/'dinov2'
    caches={m:ROOT/'outputs/p3_eigenplaces_20261010_141736_ayAvV5'/m for m in ['cosplace','eigenplaces']};caches['dinov2']=dino
    config=dict(stage='G2',development_only=True,grid=plan,predeclaration_sha256=digest(predecl),
        real_descriptor_replay_atol=2e-5,cpu_gpu_float64_score_atol=1e-12,
        old_test_selection=False,new_independent_performance_opened=False,rounding='numpy.rint, ties to even',
        optional_classic_seqslam='not executed: descriptor-score causal adaptation is labelled, not official reproduction')
    run=Run(ROOT,'g2_strong_baselines',config,dict(manifest_sha256=digest(manifest),
        cache_fingerprint_sha256={m:digest(p/'fingerprint.json') for m,p in caches.items()},predeclaration=str(predecl.relative_to(ROOT))))
    print(run.id,flush=True);update_state(ROOT,latest_run_id=run.id)
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q',
        '--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    run.command([str(ROOT/'.venv-p0/bin/python'),'experiments/temporal_vpr/g2_replay_check.py',
        '--run-dir',str(run.path)],{'PYTHONPATH':'','TORCH_HOME':str(ROOT/'weights/p0_torch')})
    records=json.loads(manifest.read_text())['records'];results=[];per_query=[];identities={}
    for role in ['train','validation']:
        score={}
        for m,cache in caches.items():
            g,gids,gfp=load_descriptors(cache,manifest,'gallery');q,qids,qfp=load_descriptors(cache,manifest,role)
            score[m]=cosine_unit_scores(q,g)
            np.save(run.path/f'{role}_{m}_scores.npy',score[m])
            identities[f'{role}_{m}']=dict(scores_sha256=digest(run.path/f'{role}_{m}_scores.npy'),
                query_ids=qids,gallery_ids=gids,cache_fp_sha256=digest(cache/'fingerprint.json'))
        qrows=canonical_rows(records,qids);grows=canonical_rows(records,gids)
        positive=index_positives(np.array([r['frame_index'] for r in qrows]),np.array([r['frame_index'] for r in grows]),5)
        mask=np.arange(len(qids))>=8
        a=score['cosplace'];b=score['eigenplaces']
        a_ranks,a_metrics=metrics_for(a,positive,mask);a_correct=positive[np.arange(len(a)),a_ranks[:,0]]
        methods=[('A-only',a,{}),('B-only',b,{}),('DINOv2-only',score['dinov2'],{}),
            ('RRF_k60',np.stack([rrf(sa,sb,60) for sa,sb in zip(a,b)]),{'k':60})]
        for weight in plan['static_AB_weights']:
            methods.append((f'AB_fixed_{weight}',(1-weight)*fixed_affine(a)+weight*fixed_affine(b),{'B_weight':weight}))
        for length in plan['L']:
            for velocities in plan['velocity_sets']:
                for weight in plan['lambda']:
                    name=f'temporal_L{length}_v'+','.join(map(str,velocities))+f'_lambda{weight}'
                    settings=dict(length=length,velocities=velocities,weight=weight)
                    methods.append((name,stream_scores(a,**settings),settings))
        # One negative control per window with the declared full velocity set.
        for length in [3,5,9]:
            settings=dict(length=length,velocities=plan['velocities'],weight=1.,shuffled=True,seed=0)
            methods.append((f'shuffled_L{length}',stream_scores(a,**settings),settings))
        for name,values,settings in methods:
            ranks,metrics=metrics_for(values,positive,mask)
            _,full=metrics_for(values,positive,np.ones(len(qids),dtype=bool))
            correct=positive[np.arange(len(a)),ranks[:,0]]
            row=dict(split=role,method=name,settings=settings,common=metrics,full_stream_with_startup=full,
                rescue=int((mask&~a_correct&correct).sum()),harm=int((mask&a_correct&~correct).sum()),
                net_gain_count=int((correct[mask].astype(int)-a_correct[mask].astype(int)).sum()),
                common_query_mask_sha256=__import__('hashlib').sha256(mask.tobytes()).hexdigest())
            results.append(row)
            for i,image_id in enumerate(qids):
                per_query.append(dict(split=role,method=name,query_image_id=image_id,common_valid=bool(mask[i]),
                    method_warmup=i<settings.get('length',1)-1,top1_gallery_image_id=gids[ranks[i,0]],
                    correct_at_1=bool(correct[i]),A_correct=bool(a_correct[i]),
                    correct_at_5=bool(positive[i,ranks[i,:5]].any()),correct_at_10=bool(positive[i,ranks[i,:10]].any()),
                    rescue=bool(not a_correct[i] and correct[i]),harm=bool(a_correct[i] and not correct[i])))
        print(json.dumps({'split':role,'methods':len(methods),'queries':len(a),'common_queries':int(mask.sum())}),flush=True)
    val=[r for r in results if r['split']=='validation' and r['method'].startswith('temporal_')]
    # Prefer fewer velocity hypotheses after L/lambda in exact ties; deterministic name last.
    key=lambda r:(-r['common']['R@1']['recall'],r['settings']['length'],r['settings']['weight'],len(r['settings']['velocities']),r['method'])
    best=sorted(val,key=key)[0]
    temporal_only=sorted([r for r in val if r['settings']['weight']==1 and r['settings']['length']>1],key=key)[0]
    fixed_nontrivial=sorted([r for r in val if r['settings']['length']>1 and r['settings']['weight']>0],key=key)[0]
    aval=next(r for r in results if r['split']=='validation' and r['method']=='A-only')
    signal=temporal_only['common']['R@1']['correct']>aval['common']['R@1']['correct']
    run.write('score_identities.json',identities)
    run.write('metrics.json',dict(development_only=True,results=results,best_temporal_grid=best,
        best_temporal_only=temporal_only,best_nontrivial_blend=fixed_nontrivial,
        decision='A' if signal else 'requires_one_bounded_alignment_speed_correction',
        no_independent_test_or_old_test_performance_computed=True))
    with (run.path/'per_query.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(per_query[0]));w.writeheader();w.writerows(per_query)
    replay=json.loads((run.path/'real_replay_checks.json').read_text());assert replay['passed']
    run.write('checks.json',dict(passed=True,causal_unit_and_original_regression_passed=True,
        real_development_replay=replay,common_query_denominators={'train':592,'validation':292},
        GT_not_online_input=True,all_grid_configurations_retained=True,
        independent_performance_unopened=True,per_query_rows=len(per_query)))
    (run.path/'interpretation.md').write_text('Cached scores measure development accuracy only. All methods share first-eight exclusion; full-stream startup is separate. Every fixed grid configuration and shuffled negative control is retained. Score range normalization is fixed affine, without test-fitted statistics. No official SeqSLAM reproduction claim. The comparison is selected on validation only; train is descriptive.\n')
    print(json.dumps({'run_id':run.id,'best_temporal_only':temporal_only,'best_blend':fixed_nontrivial,'decision': 'A' if signal else 'correction_required'}),flush=True)

if __name__=='__main__':main()
