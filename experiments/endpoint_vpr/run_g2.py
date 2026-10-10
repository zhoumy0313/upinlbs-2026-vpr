import csv,json
import numpy as np
from .runtime import ROOT,Run,state,publish,checkpoint,sha
from .datasets import seen,SL,G2
from .baselines import predictions,strong_specs
from .evaluate import evaluate,record,audit_csv

def main():
    assert state()['stages']['G1']=='passed'
    run=Run('g2_strong_baselines','strong controls and exact historical reproduction',dict(protocol_sha256=sha(ROOT/'configs/v3/v3_protocol_proposed.yaml'),grid_sha256=sha(ROOT/'configs/v3/v3_search_grid.yaml'),cached_accuracy_not_latency=True),dict(St_Lucia_identity_sha256=sha(SL/'score_identities.json'),Nordland_identity_sha256=sha(G2/'score_identities.json')));print(run.id,flush=True)
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','experiments/endpoint_vpr/tests','-q','--junitxml='+str(run.path/'tests.xml')],env={'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    ds=seen();run.write('model_identity.json',{d['dataset']+'_'+d['split']:d['model_identity'] for d in ds});run.write('canonical_manifest.json',[dict(dataset=d['dataset'],split=d['split'],q=d['q'],g=d['g'],manifest_sha256=d['manifest_sha256']) for d in ds]);specs=strong_specs()+[dict(name='R3_fixed_L9_H1_r4',kind='R1',backend='fixed_L9',H=1,r=4),dict(name='R2_fixed_L9_H1_r4_g0.5',kind='R2',backend='fixed_L9',H=1,r=4,gamma=.5)]
    old=json.loads((SL/'ranked_top50.json').read_text());aliases={'A':'A-only','B':'B-only','DINOv2':'DINOv2-only','fixed_L9':'fixed_T_best',**{f'full_L{k}':f'full_velocity_T_L{k}' for k in [3,5,9]}};historical=[];metrics=[];f=(run.path/'per_query.csv').open('w',newline='');w=None
    for d in ds:
        for spec in specs:
            p,meta=predictions(d,spec);m,rows=evaluate(d,spec,p,meta);metrics.extend(m);w=record(f,w,rows)
            if d['dataset']=='St_Lucia' and d['split']=='descriptive' and spec['name'] in aliases:
                ref=np.asarray(old['rank_indices'][aliases[spec['name']]])[:,:10];assert np.array_equal(p,ref);historical.append(dict(method=spec['name'],matched_query_top10=len(p),exact=True))
        print(d['dataset'],d['split'],'methods',len(specs),flush=True)
    f.close();audit=audit_csv(run.path/'per_query.csv',metrics)
    # Independent scalar stable rank on recorded real current similarities.
    d=next(d for d in ds if d['dataset']=='St_Lucia' and d['split']=='descriptive');s=d['scores']['cosplace'][100];assert sorted(range(len(s)),key=lambda j:(-float(s[j]),j))==np.argsort(-s,kind='stable').tolist()
    # Verify known Nordland values without changing historical outputs.
    expected={'A':210,'B':247,'fixed_L9':291,'full_L3':247,'full_L5':262,'full_L9':284}
    for name,n in expected.items():assert next(m for m in metrics if m['dataset']=='Nordland' and m['split']=='validation' and m['radius']==5 and m['method']==name)['correct']['1']==n
    run.write('independent_numeric_audit.json',audit);run.write('historical_exact_replay.json',historical);run.write('method_specs.json',specs)
    run.finish(dict(results=metrics,historical_exact=historical,methods=len(specs),Nordland_historical_counts=expected),dict(passed=True,all_ledger_counts_recomputed=True,independent_scalar_ranking_verified=True,historical_top10_exact=True,GT_not_online_input=True))
    rows=[m for m in metrics if m['dataset']=='St_Lucia' and m['split']=='validation' and m['radius']==10];tab='\n'.join(f"| {m['method']} | {m['correct']['1']}/{m['queries']} | {100*m['recall']['1']:.2f} | {m['rescue']} | {m['harm']} |" for m in rows)
    report='''# G2 acceptance\n1. Added strong_baselines run using V3 score-only Strategy, no old-source edits.\n2. Verified old score hashes and canonical image IDs; reset at each split; produce full ranking then evaluate GT offline. A is one image descriptor; T uses only prior/current scores; local policies rerank bounded indices.\n3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g2`; actual tests and CPU accuracy commands are in logs; no cached timing claims.\n4. Strong controls: single CosPlace/EigenPlaces/DINOv2, RRF, three A+B fusions, L9-v1.2, full L3/L5/L9, three global blends, shuffled and reversed controls, simple H1-r4 snap and local fixed blend.\n\n| Method | Correct | 10m % | Rescue | Harm |\n|---|---:|---:|---:|---:|\n'''+tab+'''\n\n5. Same radius-specific no-positive mask and eight-query startup exclusion; full-stream results retained. St Lucia validation is seen/exploratory.\n6. All required historical top10s agree exactly; Nordland validation counts agree with original cache runs. Independent scalar rank and CSV R@K/paired/quantile checks pass.\n7. GT rounding and video correlation prohibit pose/significance claims. No independent-test scores opened.\n8. Source/identities/CSV/logs in public archive; exact push receipt follows.\n9. Next: execute predeclared finite grid, compare P with strongest fixed and simple local controls.\n'''
    publish('g2',run,report);(ROOT/'docs/research_v3/G2_STRONG_BASELINES.md').write_text(report);oldstate=state();oldstate['stages']['G2']='passed';state(stages=oldstate['stages'],current_stage='G3',g2_run=run.id,latest_run_id=run.id);checkpoint('G2')
if __name__=='__main__':main()
