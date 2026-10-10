"""Real-image batch1 full traversals, warm20 and three synchronized CUDA passes."""
import argparse,csv,json,sys,time,resource,platform,subprocess
from pathlib import Path
import numpy as np
import torch
import joblib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.encoders.frozen import create_encoder
from evaluate_independent import load_freeze
from method_suite import Method,needed_encoders
from runtime import Run,digest,update_state

def sync(device):
    if device=='cuda':torch.cuda.synchronize()

def rss():
    fields=Path('/proc/self/status').read_text().splitlines()
    return int(next(r.split()[1] for r in fields if r.startswith('VmRSS:')))*1024

def statistic(values):
    a=np.asarray(values,dtype=float)
    return dict(mean_ms=float(a.mean()*1000),median_ms=float(np.median(a)*1000),p95_ms=float(np.percentile(a,95)*1000),measurements=len(a))

def worker(freeze,evaluation,path):
    _,f=load_freeze(freeze);path=Path(path);audit=ROOT/f['data_audit'];gallerypath=ROOT/f['gallery_build'];evaluation=ROOT/'outputs_v2'/evaluation
    rows=json.loads((audit/'manifest.json').read_text())['records'];queries=[r for r in rows if r['role']=='independent_query'];identities=json.loads((gallerypath/'gallery_identities.json').read_text())
    scoreids=json.loads((evaluation/'score_identities.json').read_text());cache={name:np.load(evaluation/(name+'_query.npy')) for name in scoreids}
    cachedscores={name:np.load(evaluation/(name+'_scores.npy')) for name in scoreids}
    for name in scoreids:assert digest(evaluation/(name+'_query.npy'))==scoreids[name]['query_array_sha256']
    pipeline=joblib.load(ROOT/f['SMR_pipeline']);measurements=[];results=[];resource_rows=[];checks=[]
    for target in f['latency_methods']:
        spec=next(s for s in f['methods'] if s['name']==target);names=needed_encoders(spec)
        before=rss();encoders={name:create_encoder(name,f['device'],(224,224)) for name in names}
        galleries={}
        for name,encoder in encoders.items():
            assert encoder.fingerprint()==identities[name]['fingerprint'];g=np.load(gallerypath/(name+'_gallery.npy')).astype(np.float64)
            galleries[name]=g/np.linalg.norm(g,axis=1,keepdims=True)
        del encoder
        sync(f['device']);loaded=rss();matcher=Method(ROOT,spec,pipeline)
        def execute(row):
            sync(f['device']);start=time.perf_counter()
            with Image.open(ROOT/row['relative_path']) as im:image=im.convert('RGB')
            decode_end=time.perf_counter();scores={};desc={};times={};score_time=0.
            for name,encoder in encoders.items():
                prepared=encoder.prepare([image]);sync(f['device']);prep_end=time.perf_counter()
                d=encoder.encode_tensor(prepared).cpu().numpy()[0];sync(f['device']);model_end=time.perf_counter()
                desc[name]=d;unit=d.astype(np.float64);unit/=np.linalg.norm(unit)
                scores[name]=np.clip(unit@galleries[name].T,-1,1);score_end=time.perf_counter()
                times[name]=dict(preprocess=prep_end-(decode_end if name==names[0] else previous_end),encoding_and_transfer=model_end-prep_end)
                score_time+=score_end-model_end;previous_end=score_end
            rank,meta=matcher.step(scores);sync(f['device']);end=time.perf_counter()
            return rank,meta,desc,scores,dict(total=end-start,decode=decode_end-start,
                preprocess=sum(t['preprocess'] for t in times.values()),encoding_and_transfer=sum(t['encoding_and_transfer'] for t in times.values()),
                similarity=score_time,history_ranking=end-previous_end)
        for row in queries[:20]:execute(row)
        matcher.reset();peak_after_warm=rss()
        if f['device']=='cuda':torch.cuda.reset_peak_memory_stats()
        method_measurements=[];max_desc=0.;max_score=0.;ranking_mismatches=0;repeat_mismatches=0;first_ranks=[]
        for repeat in range(3):
            matcher.reset();cachedmatcher=Method(ROOT,spec,pipeline);last=None;pos=0
            for i,row in enumerate(queries):
                if row['traversal']!=last:matcher.reset();cachedmatcher.reset();last=row['traversal'];pos=0
                rank,meta,desc,scores,times=execute(row)
                expected,_=cachedmatcher.step({name:cachedscores[name][i] for name in names})
                ranking_mismatches+=int(not np.array_equal(rank[:10],expected[:10]))
                for name in names:
                    max_desc=max(max_desc,float(np.max(abs(desc[name]-cache[name][i]))))
                    max_score=max(max_score,float(np.max(abs(scores[name]-cachedscores[name][i]))))
                if repeat==0:first_ranks.append(rank[:10].copy())
                else:repeat_mismatches+=int(not np.array_equal(rank[:10],first_ranks[i]))
                entry=dict(method=target,repeat=repeat,query_image_id=row['image_id'],traversal=row['traversal'],
                    traversal_position=pos,warmup=meta.get('warmup',False),**{key:value*1000 for key,value in times.items()})
                measurements.append(entry);method_measurements.append(times);pos+=1
            print('Timing',target,'pass',repeat+1,'queries',len(queries),flush=True)
        report=dict(method=target,queries_per_pass=len(queries),passes=3,warm_images=20,batch_size=1,
            total=statistic([r['total'] for r in method_measurements]),
            components={key:statistic([r[key] for r in method_measurements]) for key in ['decode','preprocess','encoding_and_transfer','similarity','history_ranking']},
            startup_included=True,gallery_build_separate=True)
        results.append(report);check=dict(method=target,max_descriptor_difference=max_desc,max_similarity_difference=max_score,
            cached_vs_real_top10_mismatches=ranking_mismatches,repeat_top10_mismatches=repeat_mismatches)
        checks.append(check)
        resource_rows.append(dict(method=target,RSS_before_models_bytes=before,RSS_loaded_bytes=loaded,RSS_after_warm_bytes=peak_after_warm,
            RSS_after_three_passes_bytes=rss(),process_highwater_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            cuda_current_allocated_bytes=int(torch.cuda.memory_allocated()) if f['device']=='cuda' else 0,
            cuda_peak_allocated_bytes=int(torch.cuda.max_memory_allocated()) if f['device']=='cuda' else 0,
            cuda_peak_reserved_bytes=int(torch.cuda.max_memory_reserved()) if f['device']=='cuda' else 0,
            offline_gallery_descriptor_bytes=sum(np.load(gallerypath/(name+'_gallery.npy')).nbytes for name in names),
            resident_float64_gallery_bytes=sum(g.nbytes for g in galleries.values()),
            score_history_bytes=(spec.get('length',1)*len(next(iter(galleries.values())))*8 if spec['kind'] in ['adaptive','temporal','smr'] else 0),
            accuracy_cache_and_audit_arrays_in_process_RSS=True))
        print(json.dumps(report),flush=True)
        del encoders,matcher,cachedmatcher,galleries
        if f['device']=='cuda':torch.cuda.empty_cache()
    hardware=dict(platform=platform.platform(),cpu=platform.processor(),torch=torch.__version__,cuda_runtime=torch.version.cuda,
        GPU=torch.cuda.get_device_name(0) if f['device']=='cuda' else None,
        nvidia_smi=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],text=True).strip() if f['device']=='cuda' else None,
        clocks_locked=False,CUDA_synchronized=f['device']=='cuda',OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1)
    (path/'metrics.json').write_text(json.dumps(dict(role='real-image online timing',freeze=freeze,results=results,hardware=hardware,resources=resource_rows,
        precision_checks=checks,latency_limitations='Sequential execution, warm file cache, clocks not locked. RSS includes accuracy audit arrays; CUDA allocator values are not total device memory. No independent statistical CI from repeats.'),indent=2))
    with (path/'per_query.csv').open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(measurements[0]));w.writeheader();w.writerows(measurements)
    passed=all(r['max_descriptor_difference']<=f['descriptor_tolerance'] and r['max_similarity_difference']<=f['score_tolerance'] and r['repeat_top10_mismatches']==0 for r in checks)
    (path/'precision_checks.json').write_text(json.dumps(dict(passed=passed,checks=checks),indent=2))
    assert passed,'Frozen precision threshold violated; retain run and report before any correction'

def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--evaluation',required=True);p.add_argument('--worker');a=p.parse_args()
    if a.worker:worker(a.freeze,a.evaluation,a.worker);return
    folder,f=load_freeze(a.freeze);run=Run(ROOT,'g4_real_online_latency',dict(freeze=a.freeze,plan=f['latency_methods'],passes=3,warm20=True,batch_size=1),
        dict(freeze_sha256=digest(folder/'freeze.json'),evaluation=a.evaluation))
    print(run.id,flush=True);update_state(ROOT,g4_latency_run=run.id,latest_run_id=run.id)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),str(Path(__file__).resolve()),'--freeze',a.freeze,'--evaluation',a.evaluation,'--worker',str(run.path)],
        {'PYTHONPATH':'','TORCH_HOME':str(ROOT/'weights/p0_torch'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
    run.write('checks.json',dict(passed=True,real_decode_and_encoding=True,all_queries_three_passes=True,warm20=True,
        precision=json.loads((run.path/'precision_checks.json').read_text())))
    (run.path/'interpretation.md').write_text('Actual decode, tensor preparation, frozen encoder batch1, CPU descriptor transfer, similarity, causal history, ranking are measured on every query. No cached scores substitute for timed computation. Audit comparisons occur after the timed interval. Three full traversals and warm20; startup included. Offline gallery build is separate. CUDA synchronized. Small speed differences are not significant; clocks not locked.\n')

if __name__=='__main__':main()
