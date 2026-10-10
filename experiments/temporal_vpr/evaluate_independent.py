"""One complete frozen independent evaluation; all methods and negative rows retained."""
import argparse,csv,json,sys,time
from pathlib import Path
import numpy as np
import torch
import joblib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.encoders.frozen import create_encoder
from runtime import Run,digest,update_state,utc_now
from causal import cosine_unit_scores
from method_suite import Method

def hit_vector(positive,ranking,k=10):
    ranks=np.asarray(ranking)[:k];hit=np.zeros(len(ranks),dtype=bool);valid=ranks>=0
    hit[valid]=np.asarray(positive)[ranks[valid]]
    return hit

def load_freeze(name):
    folder=ROOT/'freezes'/name;f=json.loads((folder/'freeze.json').read_text())
    assert f['independent_test_opened'] is False
    for name,sha in f['file_sha256'].items():assert digest(ROOT/name)==sha,name
    return folder,f

def worker(freeze,path):
    folder,f=load_freeze(freeze);path=Path(path);audit=ROOT/f['data_audit'];gallerypath=ROOT/f['gallery_build']
    records=json.loads((audit/'manifest.json').read_text())['records'];g=[r for r in records if r['role']=='gallery'];q=[r for r in records if r['role']=='independent_query']
    identities=json.loads((gallerypath/'gallery_identities.json').read_text());scores={};sourceids={}
    for name in ['cosplace','eigenplaces','dinov2']:
        gp=gallerypath/(name+'_gallery.npy');assert digest(gp)==identities[name]['array_sha256']
        assert [r['image_id'] for r in g]==identities[name]['gallery_image_ids']
        encoder=create_encoder(name,f['device'],(224,224));fp=encoder.fingerprint();assert fp==identities[name]['fingerprint']
        values=[];start=time.perf_counter()
        for i in range(0,len(q),1):
            images=[]
            for r in q[i:i+1]:
                with Image.open(ROOT/r['relative_path']) as im:images.append(im.convert('RGB'))
            values.append(encoder.encode(images))
        array=np.concatenate(values);np.save(path/(name+'_query.npy'),array)
        scores[name]=cosine_unit_scores(array,np.load(gp));np.save(path/(name+'_scores.npy'),scores[name])
        sourceids[name]=dict(query_ids=[r['image_id'] for r in q],gallery_ids=[r['image_id'] for r in g],
            query_array_sha256=digest(path/(name+'_query.npy')),score_array_sha256=digest(path/(name+'_scores.npy')),fingerprint=fp,
            extraction_seconds=time.perf_counter()-start,role='accuracy cache extraction; not online latency')
        print('Encoded independent queries',name,len(q),flush=True);del encoder
        if f['device']=='cuda':torch.cuda.empty_cache()
    (path/'score_identities.json').write_text(json.dumps(sourceids,indent=2))
    pipeline=joblib.load(ROOT/f['SMR_pipeline']);ranks={};metadata={};position=[];last=None;index=0
    for r in q:
        if last!=r['traversal']:index=0;last=r['traversal']
        position.append(index);index+=1
    for spec in f['methods']:
        method=Method(ROOT,spec,pipeline);ranking=[];metas=[];last=None
        for i,row in enumerate(q):
            if row['traversal']!=last:method.reset();last=row['traversal']
            rank,meta=method.step({name:value[i] for name,value in scores.items()});ranking.append(rank[:50]);metas.append(meta)
        ranks[spec['name']]=np.stack(ranking);metadata[spec['name']]=metas
    gc=np.array([[r['easting'],r['northing']] for r in g]);qc=np.array([[r['easting'],r['northing']] for r in q])
    distances=np.linalg.norm(qc[:,None]-gc[None],axis=2);pos=np.array(position);per=[];results=[];blocks=[]
    for radius in f['radius_m']:
        positives=distances<=radius;closed=positives.any(1);common=closed&(pos>=8)
        a=np.stack([hit_vector(positives[i],ranks['A-only'][i]) for i in range(len(q))])[:,0]
        for name,ranking in ranks.items():
            hits=np.stack([hit_vector(positives[i],ranking[i]) for i in range(len(q))]);correct=hits[:,0]
            out=dict(radius_m=radius,method=name,
                common={f'R@{k}':dict(correct=int(hits[common,:k].any(1).sum()),queries=int(common.sum()),recall=float(hits[common,:k].any(1).mean())) for k in [1,5,10]},
                full_closed_stream={f'R@{k}':dict(correct=int(hits[closed,:k].any(1).sum()),queries=int(closed.sum()),recall=float(hits[closed,:k].any(1).mean())) for k in [1,5,10]},
                rescue=int((common&~a&correct).sum()),harm=int((common&a&~correct).sum()),
                abstained_queries=int(sum(bool(m.get('abstained',False)) for i,m in enumerate(metadata[name]) if common[i])),
                excluded_no_positive=int((~closed).sum()),excluded_startup_with_positive=int((closed&(pos<8)).sum()))
            results.append(out)
            for i,row in enumerate(q):
                top=ranking[i,0];per.append(dict(radius_m=radius,method=name,query_image_id=row['image_id'],traversal=row['traversal'],
                    traversal_position=int(pos[i]),closed_valid=bool(closed[i]),common_valid=bool(common[i]),
                    exclusion='no_positive' if not closed[i] else 'shared_startup8' if pos[i]<8 else '',
                    top1_image_id='' if top<0 else g[top]['image_id'],top1_distance_m='' if top<0 else float(distances[i,top]),
                    correct_at_1=bool(hits[i,0]),correct_at_5=bool(hits[i,:5].any()),correct_at_10=bool(hits[i].any()),
                    A_correct=bool(a[i]),metadata=json.dumps(metadata[name][i])))
            if radius==25:
                for traverse in sorted({r['traversal'] for r in q}):
                    group=np.array([r['traversal']==traverse for r in q])
                    for b in range(0,max(pos[group])+1,100):
                        mask=common&group&(pos>=b)&(pos<b+100)
                        blocks.append(dict(method=name,traversal=traverse,block_start=b,queries=int(mask.sum()),
                            A_correct=int(a[mask].sum()),method_correct=int(correct[mask].sum()),
                            net_correct=int((correct[mask].astype(int)-a[mask].astype(int)).sum())))
    primary={r['method']:r for r in results if r['radius_m']==25}
    fixed=primary['fixed_T_best']['common']['R@1']['correct'];single=primary['A-only']['common']['R@1']['correct']
    outcome='B' if fixed>single else 'C'
    (path/'metrics.json').write_text(json.dumps(dict(role='new independent test, frozen protocol',freeze=freeze,results=results,
        outcome=outcome,adaptive_contribution_not_demonstrated_on_development=True,
        no_retuning=True,no_positive_query_ids=[q[i]['image_id'] for i in np.flatnonzero(~(distances<=25).any(1))],
        total_queries=len(q),gallery_images=len(g),common_queries=primary['A-only']['common']['R@1']['queries']),indent=2))
    for filename,rows in [('per_query.csv',per),('contiguous_blocks.csv',blocks)]:
        with (path/filename).open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (path/'ranked_top50.json').write_text(json.dumps(dict(query_ids=[r['image_id'] for r in q],gallery_ids=[r['image_id'] for r in g],
        rank_indices={k:v.tolist() for k,v in ranks.items()})))
    print(json.dumps(dict(outcome=outcome,primary=[{k:r[k] for k in ['method','common','rescue','harm','abstained_queries']} for r in results if r['radius_m']==25])),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--worker');a=p.parse_args()
    if a.worker:worker(a.freeze,a.worker);return
    folder,f=load_freeze(a.freeze);state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());assert not state['new_independent_test_has_been_opened']
    run=Run(ROOT,'g4_independent_evaluation',f,dict(freeze_sha256=digest(folder/'freeze.json')));print(run.id,flush=True)
    run.event('first_independent_performance_access_authorized',dict(utc=utc_now(),freeze_sha256=digest(folder/'freeze.json')))
    update_state(ROOT,new_independent_test_has_been_opened=True,first_independent_open_utc=utc_now(),g4_evaluation_run=run.id,latest_run_id=run.id)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),str(Path(__file__).resolve()),'--freeze',a.freeze,'--worker',str(run.path)],
        {'PYTHONPATH':'','TORCH_HOME':str(ROOT/'weights/p0_torch'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
    run.write('checks.json',dict(passed=True,all_methods_same_GT_and_masks=True,all_frozen_methods_run=True,source_hashes_verified=True,
        no_test_tuning=True,abstentions_are_misses=True,all_query_scores_history_kept_even_no_GT_positive=True))
    (run.path/'interpretation.md').write_text('Independent performance opened after immutable freeze. No parameters or direction will be changed from these results. All startup/no-positive exclusions explicit. Radius sensitivity was predeclared, not chosen by test score. Temporal sampling limitations and all negative controls retained.\n')

if __name__=='__main__':main()
