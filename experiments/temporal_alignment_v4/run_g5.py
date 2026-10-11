"""Frozen batch-one decoded-image latency; evaluation strictly outside timer."""
import sys,csv,json,time
import numpy as np
import torch
from PIL import Image
from runtime import *
from features import create_encoder,sync,with_scores
from algorithms import Method,predict
from protocol import load,distances,RADII
from run_g4_test import verify
def needed(spec):
    if spec['kind']=='single':return [spec['encoder']]
    return ['cosplace','eigenplaces'] if spec['kind'] in ['rrf','AB'] else ['cosplace']
def step(q,method,encoders,galleries):
    sync();start=time.perf_counter()
    with Image.open(ROOT/q['relative_path']) as im:image=im.convert('RGB')
    end=time.perf_counter();times=dict(decode_ms=(end-start)*1000,preprocess_ms=0.,encoding_transfer_ms=0.,similarity_ms=0.);previous=end;scores={}
    for name,e in encoders.items():
        prepared=e.prepare([image]);sync();prepared_end=time.perf_counter();f=e.encode_tensor(prepared).cpu().numpy()[0];sync();encoded_end=time.perf_counter();f=f.astype(np.float64);f/=np.linalg.norm(f);scores[name]=np.clip(f@galleries[name].T,-1,1);score_end=time.perf_counter()
        times['preprocess_ms']+=(prepared_end-previous)*1000;times['encoding_transfer_ms']+=(encoded_end-prepared_end)*1000;times['similarity_ms']+=(score_end-encoded_end)*1000;previous=score_end
    if 'cosplace' not in scores:scores['cosplace']=scores['eigenplaces']
    output,meta=method.step(scores,q['timestamp']);sync();end=time.perf_counter();times.update(history_ranking_ms=(end-previous)*1000,total_ms=(end-start)*1000)
    return output,meta,times
def main():
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());assert s['test_state']=='single_blind_run_complete'
    freeze=json.loads((ROOT/s['freeze_folder']/'freeze.json').read_text());verify(freeze)
    run=Run('g5_real_timing',dict(freeze_sha256=sha(ROOT/s['freeze_folder']/'freeze.json'),batch_one=True,warmup=20,full_passes=3,methods=freeze['evaluation']['timing_methods'],timing_includes='decode, preprocess, actual encoder and CPU transfer, full-gallery cosine, causal history/alignment/refinement and full stable sort, CUDA sync',accuracy='real batch-one compared against frozen batch16 cached accuracy, no method tuning'))
    encoders={};loadcost=[]
    for name in ['cosplace','eigenplaces']:
        st=time.perf_counter();e=create_encoder(name,'cuda' if torch.cuda.is_available() else 'cpu',(224,224));sync();loadcost.append(dict(encoder=name,load_seconds=time.perf_counter()-st));assert e.fingerprint()==freeze['model_identity'][name];encoders[name]=e
    results=[];offline=[]
    fieldnames=['sequence','method','repeat','query_index','query_id','total_ms','decode_ms','preprocess_ms','encoding_transfer_ms','similarity_ms','history_ranking_ms','top10','cached_top10_equal','cached_top1_equal','top1_distance_m','valid_gt','hit1_025','hit1_05','hit1_10','closed_025','closed_05','closed_10']
    with (run.path/'timing_per_query.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader()
        for seq,feature_run in [('freiburg2_pioneer_slam',s['development_feature_run']),('freiburg3_long_office_household',s['g4_run'])]:
            d=load(seq,5);cache=with_scores(seq,5,ROOT/'outputs_v4'/feature_run);dist=distances(d);gallery={}
            for name,e in encoders.items():
                arrays=[];st=time.perf_counter()
                for j in range(0,len(d['g']),16):
                    ims=[]
                    for r in d['g'][j:j+16]:
                        with Image.open(ROOT/r['relative_path']) as im:ims.append(im.convert('RGB'))
                    arrays.append(e.encode(ims))
                sync();elapsed=time.perf_counter()-st;a=np.concatenate(arrays);p=run.path/(seq+'_'+name+'_gallery.npy');np.save(p,a);g=a.astype(np.float64);g/=np.linalg.norm(g,axis=1,keepdims=True);gallery[name]=g;offline.append(dict(sequence=seq,encoder=name,batch=16,images=len(g),gallery_decode_preprocess_encode_seconds=elapsed,descriptor_bytes=int(a.nbytes),array_sha256=sha(p)))
            for spec in freeze['evaluation']['timing_methods']:
                names=needed(spec);active={n:encoders[n] for n in names};method=Method(spec,[r['timestamp'] for r in d['g']]);expected,_=predict(cache,spec)
                for q in d['q'][:20]:step(q,method,active,gallery)
                alltimes=[];allpred=[];match10=0;match1=0;components={k:[] for k in ['decode_ms','preprocess_ms','encoding_transfer_ms','similarity_ms','history_ranking_ms']}
                for repeat in range(3):
                    method.reset();preds=[]
                    for i,q in enumerate(d['q']):
                        o,meta,times=step(q,method,active,gallery);p=o[:10];preds.append(p);alltimes.append(times['total_ms']);equal10=bool(np.array_equal(p,expected[i]));equal1=int(p[0])==int(expected[i,0]);match10 += int(equal10);match1 += int(equal1)
                        for k in components:components[k].append(times[k])
                        row=dict(sequence=seq,method=spec['name'],repeat=repeat,query_index=i,query_id=q['image_id'],top10=json.dumps(p.tolist()),cached_top10_equal=int(equal10),cached_top1_equal=int(equal1),top1_distance_m=float(dist[i,p[0]]) if q['valid_gt'] else '',valid_gt=int(q['valid_gt']),**times)
                        for r,suffix in [(.25,'025'),(.5,'05'),(1.,'10')]:row['hit1_'+suffix]=int(dist[i,p[0]]<=r);row['closed_'+suffix]=int(np.any(dist[i]<=r))
                        writer.writerow(row)
                    allpred.append(np.stack(preds))
                valid=np.array([q['valid_gt'] for q in d['q']]);accuracy=[]
                for r in RADII:
                    positive=dist<=r;closed=positive.any(axis=1)&valid
                    accuracy.append(dict(radius_m=r,closed_queries=int(closed.sum()),correct1_per_pass=[int(positive[np.arange(len(d['q'])),p[:,0]][closed].sum()) for p in allpred]))
                result=dict(sequence=seq,method=spec['name'],kind=spec['kind'],queries=len(d['q']),passes=3,timed_intervals=len(alltimes),warmup=20,batch=1,mean_ms=float(np.mean(alltimes)),median_ms=float(np.median(alltimes)),P95_ms=float(np.percentile(alltimes,95)),component_mean_ms={k:float(np.mean(v)) for k,v in components.items()},cached_top10_mismatches=len(alltimes)-match10,cached_top1_mismatches=len(alltimes)-match1,repeat_top10_mismatches=[int(np.any(allpred[j]!=allpred[0],axis=1).sum()) for j in [1,2]],actual_online_accuracy=accuracy)
                results.append(result);print(json.dumps(dict(sequence=seq,method=spec['name'],mean_ms=result['mean_ms'],cached_top1_mismatch=result['cached_top1_mismatches'])),flush=True)
    # Independently aggregate emitted CSV, no copied timer summaries.
    grouped={}
    with (run.path/'timing_per_query.csv').open() as f:
        for row in csv.DictReader(f):grouped.setdefault((row['sequence'],row['method']),[]).append(row)
    for result in results:
        rows=grouped[result['sequence'],result['method']];times=np.array([float(r['total_ms']) for r in rows]);assert len(rows)==result['timed_intervals'] and abs(times.mean()-result['mean_ms'])<1e-10 and abs(np.percentile(times,95)-result['P95_ms'])<1e-10
        for r,suffix in [(.25,'025'),(.5,'05'),(1.,'10')]:
            actual=[sum(int(x['hit1_'+suffix]) for x in rows if int(x['repeat'])==rep and x['closed_'+suffix]=='1') for rep in range(3)];assert actual==next(a['correct1_per_pass'] for a in result['actual_online_accuracy'] if a['radius_m']==r)
    result=dict(run_id=run.id,results=results,offline_gallery=offline,model_load=loadcost,freeze_sha256=sha(ROOT/s['freeze_folder']/'freeze.json'),numeric_csv_audit_passed=True,peak_RSS_bytes=int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmHWM:')))*1024,torch_peak_allocated_cuda_bytes=int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else None,total_real_timed_queries=sum(r['timed_intervals'] for r in results),model_identity=freeze['model_identity'],no_retuning=True)
    write(ROOT/'docs/research_v4/REAL_TIMING_RESULTS.json',result)
    (ROOT/'docs/research_v4/G5_TIMING_ACCEPTANCE.md').write_text('# G5 real-image timing — passed\n\nBoth developer and independent query streams measured using actual RGB decoding, batch-one frozen inference, CPU transfer, full-gallery cosine, current/past temporal processing, refinement and full ranking with CUDA synchronization. Twenty actual-image warmups per method, then reset causal history and three complete ordered passes. Gallery encoding/model initialization separated. Timing CSV independently reaggregated; all batch16 cached-vs-batch1 and repeat mismatches and actual per-pass accuracy retained, no parameters changed. Invalid-GT queries are timed and remain in causal history. Main numeric accuracy remains explicitly batch16 extraction; online actual batch1 accuracy is a separate audited measurement. No open-set rejection claim. Paper/report iteration follows with all figures/numbers bound to this evidence.\n')
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());s.update(g5_timing_run=run.id,current_stage='G5 paper');write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    run.finish(result,passed=False);run.checkpoint('G5 genuine batch-one image pipeline timing and accuracy audit')
if __name__=='__main__':main()
