import csv,json
import numpy as np
from .core import rank
from .baselines import predictions

def evaluate(d,spec,pred,metadata):
    qn=len(d['q']);mask=np.arange(qn)>=8;distance=d['distance'];a=d.get('_A_top1')
    if a is None:a=np.array([rank(s)[0] for s in d['scores']['cosplace']]);d['_A_top1']=a
    rows=[];metrics=[]
    dd=distance[np.arange(qn)[:,None],pred]
    for radius in d['radii']:
        has=(distance<=radius).any(axis=1);valid=mask&has;hits=dd<=radius;ac=distance[np.arange(qn),a]<=radius
        if not valid.any():raise ValueError('No common eligible queries')
        correct=hits[:,0];rescue=int((valid&~ac&correct).sum());harm=int((valid&ac&~correct).sum());net=int(correct[valid].sum()-ac[valid].sum());assert rescue-harm==net
        counts=[int(hits[valid,:k].any(axis=1).sum()) for k in [1,5,10]];assert counts==sorted(counts)
        vals=dd[valid,0];metric=dict(dataset=d['dataset'],split=d['split'],unit=d['unit'],method=spec['name'],settings=spec,radius=radius,queries=int(valid.sum()),correct=dict(zip(['1','5','10'],counts)),recall=dict(zip(['1','5','10'],[v/int(valid.sum()) for v in counts])),rescue=rescue,harm=harm,net=net,no_positive=int((~has).sum()),startup_excluded=8,full_stream_correct=int(correct[has].sum()),full_stream_queries=int(has.sum()),distance_median=float(np.median(vals)),distance_P90=float(np.percentile(vals,90)),distance_P95=float(np.percentile(vals,95)),near_boundary_2m=int((abs(vals-radius)<=2).sum()) if d['unit']=='metres' else None)
        metrics.append(metric)
        for i,q in enumerate(d['q']):
            meta=metadata[i];rows.append(dict(dataset=d['dataset'],split=d['split'],unit=d['unit'],method=spec['name'],radius=radius,query_index=i,query_id=q['image_id'],common_valid=int(valid[i]),no_positive=int(not has[i]),startup=int(i<8),top10_indices=json.dumps(pred[i].tolist()),top10_ids=json.dumps([d['g'][j]['image_id'] for j in pred[i]]),top10_distances=json.dumps(dd[i].tolist()),top10_scores=json.dumps(meta['top10_scores']),correct1=int(correct[i]),correct5=int(hits[i,:5].any()),correct10=int(hits[i].any()),A_correct=int(ac[i]),rescue=int(not ac[i] and correct[i]),harm=int(ac[i] and not correct[i]),endpoint_offset_vs_A=int(pred[i,0]-a[i]),candidates=json.dumps(meta['candidates']),eligible=json.dumps(meta['eligible']),T_top3=json.dumps(meta['T_top3']),T_top3_scores=json.dumps(meta['T_top3_scores']),path_offsets=json.dumps(meta['path_offsets']),winning_paths=json.dumps(meta.get('winning_paths',[])),fallback_reason=meta['fallback_reason'],method_warmup=int(meta['warmup'])))
    return metrics,rows

def writer(path):
    f=path.open('w',newline='');return f,None

def record(f,w,rows):
    if w is None:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
    w.writerows(rows);return w

def audit_csv(path,metrics):
    """Separate CSV reaggregation with scalar Python sorts/thresholds and quantiles."""
    groups={}
    with path.open() as f:
        for r in csv.DictReader(f):
            if r['common_valid']!='1':continue
            ds=json.loads(r['top10_distances']);rad=float(r['radius']);hits=[float(x)<=rad for x in ds];assert int(r['correct1'])==hits[0];assert int(r['correct5'])==any(hits[:5]);assert int(r['correct10'])==any(hits)
            key=(r['dataset'],r['split'],r['method'],rad);g=groups.setdefault(key,dict(n=0,counts=[0,0,0],rescue=0,harm=0,dist=[]));g['n']+=1
            for k,K in enumerate([1,5,10]):g['counts'][k]+=any(hits[:K])
            ac=int(r['A_correct']);g['rescue']+=not ac and hits[0];g['harm']+=ac and not hits[0];g['dist'].append(ds[0])
    for m in metrics:
        g=groups[(m['dataset'],m['split'],m['method'],float(m['radius']))];assert g['n']==m['queries'];assert g['counts']==list(m['correct'].values());assert g['rescue']==m['rescue'] and g['harm']==m['harm'];assert g['rescue']-g['harm']==m['net'];assert abs(np.median(g['dist'])-m['distance_median'])<1e-9
        for K in [1,5,10]:assert abs(m['recall'][str(K)]-g['counts'][[1,5,10].index(K)]/g['n'])<1e-12
        if m['unit']=='metres':assert sum(abs(v-m['radius'])<=2 for v in g['dist'])==m['near_boundary_2m']
        for p in [90,95]:assert abs(np.percentile(g['dist'],p)-m[f'distance_P{p}'])<1e-9
    return dict(passed=True,groups=len(groups),all_R1_R5_R10_and_rescue_harm_and_distance_quantiles_recomputed=True)
