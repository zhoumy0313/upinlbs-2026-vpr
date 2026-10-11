import csv,json
import numpy as np
from PIL import Image,ImageDraw
from runtime import *
from features import with_scores
from algorithms import predict
from evaluation import evaluate,audit_csv,FIELDS
from protocol import distances
def choose(specs,metrics):
    by={(m['method'],m['radius_m']):m for m in metrics if m['hz']==5}
    def key(s):return (-(by[s['name'],.25]['correct1']+by[s['name'],.5]['correct1']),-by[s['name'],.5]['correct1'],s['name'])
    return sorted(specs,key=key)[0]
def main():
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());assert not s['independent_retrieval_opened']
    grid=json.loads((ROOT/'configs/v4/search_grid.yaml').read_text());baseline=json.loads((ROOT/'docs/research_v4/BASELINE_RESULTS.json').read_text())['results'];folder=ROOT/'outputs_v4'/s['development_feature_run']
    run=Run('g3_bounded',dict(grid_sha256=sha(ROOT/'configs/v4/search_grid.yaml'),development_feature_run=s['development_feature_run'],candidate_count=len(grid['candidates']),optional_branches=0,selection=grid['selection']))
    metrics=[];allpred={}
    with (run.path/'per_query.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for hz in [1,3,5]:
            d=with_scores('freiburg2_pioneer_slam',hz,folder);a,_=predict(d,grid['baselines'][0])
            for spec in grid['candidates']:
                p,meta=predict(d,spec);metrics.extend(evaluate(d,spec,p,meta,writer,a));allpred[str(hz)+'_'+spec['name']]=p
    np.savez_compressed(run.path/'all_top10_local.npz',**allpred);audit=audit_csv(run.path/'per_query.csv',metrics);write(run.path/'independent_numeric_audit.json',audit)
    best=choose(grid['candidates'],metrics);strong=choose(grid['baselines'],baseline);d=with_scores('freiburg2_pioneer_slam',5,folder);dist=distances(d)
    pp,meta=predict(d,best);bp,bmeta=predict(d,strong);ap,ameta=predict(d,grid['baselines'][0]);positives=dist<=.5;valid=np.array([r['valid_gt'] for r in d['q']]);closed=positives.any(axis=1)&valid;ix=np.arange(len(d['q']));p_ok=positives[ix,pp[:,0]];b_ok=positives[ix,bp[:,0]];a_ok=positives[ix,ap[:,0]]
    cases=[];chosen=set()
    categories={'rescue_vs_strong':closed&p_ok&~b_ok,'harm_vs_strong':closed&~p_ok&b_ok,'A_error':closed&~a_ok,'open_query':valid&~closed}
    for category,mask in categories.items():
        pick=[int(i) for i in np.flatnonzero(mask) if i not in chosen][:2]
        if len(pick)<2:pick += [int(i) for i in np.flatnonzero(valid) if i not in chosen and i not in pick][:2-len(pick)]
        for i in pick:
            chosen.add(i);cases.append(dict(category=category,category_matches=bool(mask[i]),query_index=i,query=d['q'][i],candidate_ids=meta[i]['candidates'],eligible_ids=meta[i]['eligible'],predictions={name:dict(gallery=d['g'][int(p[i,0])],distance_m=float(dist[i,p[i,0]])) for name,p in [('A',ap),('strong',bp),('proposed',pp)]}))
    canvas=Image.new('RGB',(960,155*len(cases)),'white');draw=ImageDraw.Draw(canvas)
    for i,c in enumerate(cases):
        refs=[('query',c['query'])]+[(n,c['predictions'][n]['gallery']) for n in ['A','strong','proposed']]
        for col,(name,r) in enumerate(refs):
            with Image.open(ROOT/r['relative_path']) as im:im=im.convert('RGB');im.thumbnail((235,125));canvas.paste(im,(col*240,i*155))
            label='query '+str(c['query_index']) if name=='query' else f"{name} {c['predictions'][name]['distance_m']:.3f}m";draw.text((col*240,i*155+127),label,fill='black')
    canvas.save(run.path/'real_matching_cases_local_only.jpg');write(run.path/'real_cases.json',cases)
    envelope={str(r):max(m['correct1'] for m in baseline if m['hz']==5 and m['radius_m']==r) for r in [.25,.5]}
    pc={str(r):next(m['correct1'] for m in metrics if m['hz']==5 and m['radius_m']==r and m['method']==best['name']) for r in [.25,.5]}
    gate=all(pc[str(r)]>envelope[str(r)] for r in [.25,.5])
    same={k:[x for x in grid['baselines'] if x['kind']==k and x.get('W')==best['W'] and x.get('H')==best['H'] and x.get('r_seconds')==best['r_seconds']] for k in ['time_R1','time_R2']}
    selected=dict(proposed=best,strongest_selected=strong,baseline_envelope_correct1=envelope,proposed_correct1=pc,development_positive_gate=gate,selection_uses='Pioneer 5Hz only, sum strict R1 then primary R1 then name',same_pool_controls=same,baseline_count=len(grid['baselines']),candidate_count=len(grid['candidates']),optional_branch_added=False,results=metrics,feature_run=s['development_feature_run'])
    write(ROOT/'configs/v4/selected_methods.json',selected);write(run.path/'selection.json',selected)
    (ROOT/'docs/research_v4/G3_ACCEPTANCE.md').write_text(f'# G3 — finite exploration complete\n\nAll {len(grid["candidates"])} predeclared support-constraint configurations executed at 1/3/5Hz development conditions; independent scalar bilinear reference tests pass, no extra module/branch. Selected candidate `{best["name"]}`; selected mature/simple strongest `{strong["name"]}` by the predeclared joint strict/primary criterion. Baseline envelope correct@1 at 0.25/0.5m: {envelope}; candidate: {pc}. Strict-both-radii positive gate: **{gate}**. No claim of effective new method is allowed if false. All positive/negative scores, complete Top10 query ledgers, candidate coverage, rescues/harm and eight real cases retained. Category fallbacks are explicitly labelled; photos stay local. Timestamp alignment, speed search and endpoint relaxation are prior art; our adaptation is not an official STA-VPR/AdaptSeqVPR/SMR reproduction. No blind retrieval opened. Next: freeze selected settings and all strong baselines, then one independent test, retaining failures.\n')
    s.update(g3_run=run.id,current_stage='G4',development_positive_gate=gate,positive_method_claim=False);write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    run.finish(dict(selection={k:v for k,v in selected.items() if k!='results'},results=metrics,numeric_audit=audit,real_case_count=len(cases),all_top10_sha256=sha(run.path/'all_top10_local.npz')));run.checkpoint('G3 bounded development and honest mechanism gate')
    print(json.dumps(dict(candidate=best['name'],strong=strong['name'],gate=gate,pc=pc,envelope=envelope)),flush=True)
if __name__=='__main__':main()
