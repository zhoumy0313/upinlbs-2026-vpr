import argparse,csv,json,resource,sys,time,subprocess
import numpy as np
import torch
from PIL import Image
from .runtime import ROOT,Run,sha,state,publish,checkpoint
from .datasets import seen,SL
from .baselines import predictions
from .evaluate import evaluate,record,audit_csv
from .online import Online,needed,sync,create_encoder

# Read the Linux process field directly; no secrets/environment dump.
def rss():return int(next(x.split()[1] for x in __import__('pathlib').Path('/proc/self/status').read_text().splitlines() if x.startswith('VmRSS:')))*1024

def worker(folder,path):
    path=__import__('pathlib').Path(path);f=json.loads((ROOT/folder/'freeze.json').read_text());torch.set_num_threads(1);torch.set_num_interop_threads(1);assert torch.cuda.is_available()
    for rel,h in f['science_file_sha256'].items():assert sha(ROOT/rel)==h,rel
    d=next(d for d in seen() if d['dataset']=='St_Lucia' and d['split']=='descriptive');tr=[r['traversal'] for r in d['g']];modelids=json.loads((ROOT/folder/'model_identity.json').read_text());galleries={};offline=[]
    for name in ['cosplace','eigenplaces','dinov2']:
        start=time.perf_counter();encoder=create_encoder(name,'cuda',(224,224));sync();loadsecs=time.perf_counter()-start;assert encoder.fingerprint()==modelids[name];start=time.perf_counter();arrays=[]
        for i in range(0,len(d['g']),16):
            images=[]
            for r in d['g'][i:i+16]:
                with Image.open(ROOT/r['relative_path']) as im:images.append(im.convert('RGB'))
            arrays.append(encoder.encode(images))
        sync();elapsed=time.perf_counter()-start;g=np.concatenate(arrays);np.save(path/(name+'_gallery.npy'),g);g=g.astype(np.float64);g/=np.linalg.norm(g,axis=1,keepdims=True);galleries[name]=g;offline.append(dict(encoder=name,model_load_seconds=loadsecs,actual_gallery_encode_seconds=elapsed,images=len(g),batch=16,array_sha256=sha(path/(name+'_gallery.npy')),fingerprint=modelids[name],descriptor_bytes=int(g.nbytes)));del encoder;torch.cuda.empty_cache();print('Gallery',name,elapsed,flush=True)
    metrics=[];timings=[];checks=[];resources=[];af=(path/'per_query.csv').open('w',newline='');aw=None;tf=(path/'latency_measurements.csv').open('w',newline='');tw=None
    for spec in f['methods']:
        names=needed(spec);before=rss();start=time.perf_counter();encoders={name:create_encoder(name,'cuda',(224,224)) for name in names};sync();loadtime=time.perf_counter()-start
        for name,e in encoders.items():assert e.fingerprint()==modelids[name]
        online=Online(spec,tr,{name:galleries[name] for name in names},encoders);expected,_=predictions(d,spec)
        for r in d['q'][:20]:online.step(ROOT/r['relative_path'])
        torch.cuda.reset_peak_memory_stats();values=[];first=[];metas=[];maxscore=0.;mismatches=0;repeatmismatch=0
        for repeat in range(3):
            online.reset()
            for i,row in enumerate(d['q']):
                p,meta,desc,scores,times=online.step(ROOT/row['relative_path']);values.append(times['total']*1000)
                if repeat==0:first.append(p[:10].copy());metas.append(meta)
                else:repeatmismatch+=int(not np.array_equal(p[:10],first[i]))
                mismatches+=int(not np.array_equal(p[:10],expected[i]))
                for name in names:maxscore=max(maxscore,float(abs(scores[name]-d['scores'][name][i]).max()))
                entry=dict(method=spec['name'],repeat=repeat,query_index=i,query_id=row['image_id'],startup=int(i<8),**{k:v*1000 for k,v in times.items()})
                if tw is None:tw=csv.DictWriter(tf,fieldnames=list(entry));tw.writeheader()
                tw.writerow(entry)
            tf.flush();print('Timing',spec['name'],'pass',repeat+1,'/',3,flush=True)
        result=dict(method=spec['name'],mean_ms=float(np.mean(values)),median_ms=float(np.median(values)),P95_ms=float(np.percentile(values,95)),measurements=len(values),queries_per_pass=len(d['q']),passes=3,warmup20=True,batch1=True,actual_images_encoded=True,includes_decode_to_complete_ranking=True,model_load_seconds=loadtime,startup_included=True)
        timings.append(result);checks.append(dict(method=spec['name'],score_difference_max=maxscore,cached_top10_mismatches=mismatches,repeat_top10_mismatches=repeatmismatch,passed=maxscore<=f['score_atol'] and repeatmismatch==0));m,rows=evaluate(d,spec,np.stack(first),metas);metrics.extend(m);aw=record(af,aw,rows);af.flush()
        resources.append(dict(method=spec['name'],process_RSS_before_model_bytes=before,process_RSS_after_bytes=rss(),process_highwater_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,CUDA_peak_allocated_bytes=torch.cuda.max_memory_allocated(),CUDA_peak_reserved_bytes=torch.cuda.max_memory_reserved(),RSS_includes_accuracy_audit_arrays=True));print(json.dumps(result),flush=True);del encoders,online;torch.cuda.empty_cache()
    af.close();tf.close();audit=audit_csv(path/'per_query.csv',metrics)
    # Independently reaggregate all true measured intervals from CSV.
    vals={}
    with (path/'latency_measurements.csv').open() as fcsv:
        for r in csv.DictReader(fcsv):vals.setdefault(r['method'],[]).append(float(r['total']))
    for r in timings:
        v=vals[r['method']];assert len(v)==r['measurements'];assert abs(sum(v)/len(v)-r['mean_ms'])<1e-9;assert abs(np.percentile(v,95)-r['P95_ms'])<1e-9
    out=dict(results=metrics,timing=timings,offline_gallery=offline,resources=resources,precision_checks=checks,independent_status='INDEPENDENT_TEST_UNAVAILABLE',data_role='seen_only',hardware=dict(GPU=torch.cuda.get_device_name(0),torch=torch.__version__,CUDA_runtime=torch.version.cuda,threads=1,CUDA_synchronized=True,clocks_locked=False),audit=audit,all_checks_passed=all(c['passed'] for c in checks))
    (path/'worker_metrics.json').write_text(json.dumps(out,indent=2));assert out['all_checks_passed'],'Precision/repeat discrepancy; preserve complete run before repair'

def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--freeze');a=p.parse_args()
    if a.worker:worker(a.freeze,a.worker);return
    st=state();assert st['stages']['G4']=='passed_seen_only_independent_unavailable';folder=st['freeze_directory'];f=json.loads((ROOT/folder/'freeze.json').read_text());run=Run('g5_real_online','frozen complete seen-only real-image accuracy/timing, no new external test',f,dict(freeze_sha256=sha(ROOT/folder/'freeze.json')));print(run.id,flush=True);state(g5_run=run.id,latest_run_id=run.id)
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','experiments.endpoint_vpr.run_g5','--worker',str(run.path),'--freeze',folder],env={'PYTHONPATH':'','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','TORCH_HOME':str(ROOT/'weights/p0_torch')});m=json.loads((run.path/'worker_metrics.json').read_text());run.write('model_identity.json',json.loads((ROOT/folder/'model_identity.json').read_text()));run.write('canonical_manifest.json',json.loads((ROOT/folder/'manifest.json').read_text()));run.finish(m,dict(passed=m['all_checks_passed'],CSV_accuracy_and_timing_independently_recomputed=True,new_independent_test='not_run_source_unavailable',real_batch1_three_full_passes=True))
    report='''# G5 acceptance\n1. Added actual image Online pipeline and immutable real timing run.\n2. Each image is reopened/decoded, each required frozen encoder runs at batch1, descriptor transfers to CPU, exact similarity computed, causal history updated and complete gallery sorted. GPS is evaluation-only.\n3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g5`; worker runs with OMP/BLAS/PyTorch threads=1 and CUDA synchronization. 20 warm images + three full 1464-query passes for every frozen comparison, startup included. Gallery encoding and model loading measured separately.\n4. All methods R@1/5/10 and 10/25/5/15/50m labels from first real pass; paired counts/quantiles and measured mean/median/P95 are independently rebuilt from CSV. RSS, CUDA allocated/reserved separate.\n5. Frozen method/mask/GT/model parameters, no changes using outcomes; all data explicitly seen.\n6. INDEPENDENT_TEST_UNAVAILABLE: no external recall invented; real timing and seen audit executed. Development mechanism judgment remains unchanged.\n7. Warm OS cache/unlocked clocks/correlated video; small latency deltas are descriptive, no deployment or significance claim.\n8. Source/raw timings/real prediction ledger/negative controls/failures/hashes archived; push follows.\n9. Next: evidence-driven V3 manuscript versions and numeric/literature/PDF audit, retain working_draft if external validation absent.\n'''
    publish('g5',run,report);st['stages']['G5']='passed_seen_timing_independent_not_run';state(stages=st['stages'],current_stage='G6',g5_run=run.id,latest_run_id=run.id);checkpoint('G5')
if __name__=='__main__':main()
