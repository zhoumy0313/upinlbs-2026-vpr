"""Separate offline-only metre evaluator, complete query ledgers and audits."""
import csv,json
import numpy as np
from protocol import distances,RADII
from runtime import write
FIELDS=['sequence','hz','method','kind','radius_m','query_index','query_id','timestamp','valid_gt','closed','open','attempted','rejected','top10','top1_distance_m','hit1','hit5','hit10','A_hit1','rescue','harm','candidate_count','candidate_positive','candidate_ids','eligible_ids','startup']
def evaluate(d,spec,pred,metadata,writer,a_pred):
    dist=distances(d);valid=np.array([r['valid_gt'] for r in d['q']]);metrics=[];qn=len(d['q']);ix=np.arange(qn)
    for radius in RADII:
        positive=dist<=radius;closed=valid&positive.any(axis=1);opened=valid&~closed
        hit={k:np.any(np.take_along_axis(positive,pred[:,:k],axis=1),axis=1) for k in [1,5,10]};ahit=positive[ix,a_pred[:,0]]
        topdist=dist[ix,pred[:,0]];rescue=closed&hit[1]&~ahit;harm=closed&~hit[1]&ahit
        coverage=np.array([bool(positive[i,m['candidates']].any()) if m['candidates'] else False for i,m in enumerate(metadata)])
        n=int(closed.sum());result=dict(sequence=d['sequence'],hz=d['hz'],method=spec['name'],kind=spec['kind'],radius_m=radius,total_queries=qn,valid_gt_queries=int(valid.sum()),invalid_gt_queries=int((~valid).sum()),closed_queries=n,open_queries=int(opened.sum()),attempted=int(valid.sum()),rejected=0,attempt_coverage=1.0,closed_coverage=float(n/valid.sum()),correct1=int(hit[1][closed].sum()),correct5=int(hit[5][closed].sum()),correct10=int(hit[10][closed].sum()),R1=float(hit[1][closed].mean()) if n else None,R5=float(hit[5][closed].mean()) if n else None,R10=float(hit[10][closed].mean()) if n else None,rescue=int(rescue.sum()),harm=int(harm.sum()),A_correct1=int(ahit[closed].sum()),top1_distance_median_all_valid=float(np.median(topdist[valid])),top1_distance_P90_all_valid=float(np.percentile(topdist[valid],90)),top1_distance_median_closed=float(np.median(topdist[closed])) if n else None,top1_distance_P90_closed=float(np.percentile(topdist[closed],90)) if n else None,candidate_positive_closed=int(coverage[closed].sum()),candidate_positive_A_errors=int((coverage&closed&~ahit).sum()),open_false_accepts=int(opened.sum()),rejection_policy='none; not an open-set detector')
        assert result['correct1']-result['A_correct1']==result['rescue']-result['harm'] and result['correct1']<=result['correct5']<=result['correct10']
        metrics.append(result)
        for i,q in enumerate(d['q']):
            m=metadata[i];writer.writerow(dict(sequence=d['sequence'],hz=d['hz'],method=spec['name'],kind=spec['kind'],radius_m=radius,query_index=i,query_id=q['image_id'],timestamp=q['timestamp'],valid_gt=int(valid[i]),closed=int(closed[i]),open=int(opened[i]),attempted=int(valid[i]),rejected=0,top10=json.dumps(pred[i].tolist()),top1_distance_m=float(topdist[i]) if valid[i] else '',hit1=int(hit[1][i]),hit5=int(hit[5][i]),hit10=int(hit[10][i]),A_hit1=int(ahit[i]),rescue=int(rescue[i]),harm=int(harm[i]),candidate_count=len(m['candidates']),candidate_positive=int(coverage[i]),candidate_ids=json.dumps(m['candidates']),eligible_ids=json.dumps(m['eligible']),startup=int(m['startup'])))
    return metrics
def audit_csv(path,metrics):
    groups={}
    with open(path) as f:
        for r in csv.DictReader(f):
            key=(r['sequence'],int(r['hz']),r['method'],float(r['radius_m']));g=groups.setdefault(key,[]);g.append(r)
    checks=[]
    for m in metrics:
        key=(m['sequence'],m['hz'],m['method'],m['radius_m']);rows=groups[key];closed=[r for r in rows if r['closed']=='1'];valid=[r for r in rows if r['valid_gt']=='1']
        assert len(rows)==m['total_queries'] and len(closed)==m['closed_queries'] and len(valid)==m['valid_gt_queries']
        for k in [1,5,10]:assert sum(int(r['hit'+str(k)]) for r in closed)==m['correct'+str(k)]
        assert sum(int(r['rescue']) for r in rows)==m['rescue'] and sum(int(r['harm']) for r in rows)==m['harm']
        checks.append(dict(key=list(key),rows=len(rows),passed=True))
    return dict(passed=True,metric_groups=len(checks),row_count=sum(len(v) for v in groups.values()),checks=checks)
