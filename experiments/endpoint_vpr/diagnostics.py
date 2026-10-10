"""Case selection follows prior traversal-order rule; GT is offline diagnostics only."""
import json
import numpy as np
from PIL import Image,ImageDraw
from .runtime import ROOT,Run,state,publish,sha
from .datasets import seen
from .baselines import predictions,strong_specs
from .core import Temporal,candidates

def main():
    run=Run('g1_case_audit','correct H1 empty-neighborhood examples; preserve original failed category records',dict(prior_case_rule='first two per category in traversal order',correction='unrepairable r16 is centered at Top1/H1; initial visualization mistakenly used H3 and correctly flagged no matches',changes_to_predictions_or_parameters=False));print(run.id,flush=True)
    d=next(d for d in seen() if d['dataset']=='St_Lucia' and d['split']=='descriptive');specs=[s for s in strong_specs() if s['name'] in ['A','fixed_L9','full_L3','full_L5','full_L9']];out={s['name']:predictions(d,s)[0] for s in specs};tr=[r['traversal'] for r in d['g']];m=Temporal();T=np.stack([m.step(row,tr)[0] for row in d['scores']['cosplace']]);dist=d['distance'];n=len(d['q']);mask=np.arange(n)>=8;a=dist[np.arange(n),out['A'][:,0]]<=10;t=dist[np.arange(n),out['fixed_L9'][:,0]]<=10
    cv={r:np.array([bool((dist[i,candidates(T[i],1,r,tr)]<=10).any()) for i in range(n)]) for r in [4,16]}
    cats={'repairable_H1_r4':mask&~t&cv[4],'unrepairable_H1_r16':mask&~t&~cv[16],'A_correct_T_wrong':mask&a&~t,'multiwindow_disagreement':mask&(out['full_L3'][:,0]!=out['full_L9'][:,0])};selected=set();cases=[]
    for label,available in cats.items():
        picks=[int(i) for i in np.flatnonzero(available) if i not in selected][:2];assert len(picks)==2,label
        for i in picks:
            selected.add(i);cases.append(dict(category=label,category_matches=True,available=int(available.sum()),query_index=i,query=d['q'][i],predictions={name:dict(index=int(p[i,0]),gallery=d['g'][p[i,0]],distance_m=float(dist[i,p[i,0]])) for name,p in out.items()}))
    canvas=Image.new('RGB',(960,1240),'white');draw=ImageDraw.Draw(canvas)
    for rownum,c in enumerate(cases):
        refs=[('query',c['query'])]+[(name,c['predictions'][name]['gallery']) for name in ['A','fixed_L9','full_L3']]
        for col,(name,r) in enumerate(refs):
            im=Image.open(ROOT/r['relative_path']).convert('RGB');im.thumbnail((235,125));canvas.paste(im,(col*240,rownum*155));label=f"q{c['query_index']} {c['category']}" if name=='query' else f"{name} {c['predictions'][name]['distance_m']:.1f}m";draw.text((col*240,rownum*155+127),label,fill='black')
    canvas.save(run.path/'figures/real_cases_local_only.jpg');run.write('cases.json',cases);run.write('canonical_manifest.json',dict(q=d['q'],g=d['g']));run.write('model_identity.json',d['model_identity']);run.finish(dict(real_case_count=8,all_categories_have_actual_matches=True,cases=cases),dict(passed=True,no_selection_or_prediction_changed=True))
    publish('g1_cases',run,'# G1 case audit\nThe initial H3/r16 visualization category had no matching queries and explicitly saved category_matches=false. It must not be cited as a true negative. H1/r16, the Top1-centered neighborhood required for the drift analysis, has three genuinely uncovered errors. This supplement uses the originally declared first-two-in-order rule for four categories; all eight now satisfy their named category. Original run/figure remains preserved, no algorithm or threshold changed. Actual case IDs, hashes and distances accompany the supplement. Photos remain local and are not redistributed. Next: continue the predeclared grid, with no independent predictions opened.')
    (ROOT/'docs/research_v3/ERROR_CASES.md').open('a').write('\n## Authoritative case audit correction\nOriginal unrepairable_r16 rows were explicitly category_matches=false because H3/r16 covered all errors; those rows are fallback examples, not true negatives. Use '+run.id+' for all eight category-matched examples, centered on H1 for r16 negatives.\n'+'\n'.join(f"- {c['category']}: q{c['query_index']}; "+', '.join(f"{name}={c['predictions'][name]['distance_m']:.2f}m" for name in ['A','fixed_L9','full_L3']) for c in cases)+'\n');state(g1_case_audit_run=run.id)
if __name__=='__main__':main()
