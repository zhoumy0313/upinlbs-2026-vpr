"""Replay development caches through the common deployment factory before independent test."""
import csv,json
from pathlib import Path
import numpy as np
import joblib
from runtime import Run,digest,update_state
from method_suite import Method,specifications
ROOT=Path(__file__).resolve().parents[2]

def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());assert not state['new_independent_test_has_been_opened']
    paths={key:ROOT/'outputs_v2'/state[key] for key in ['g2_baseline_run','g3_adaptive_run','g3_smr_run']}
    g2=json.loads((paths['g2_baseline_run']/'metrics.json').read_text());g3=json.loads((paths['g3_adaptive_run']/'metrics.json').read_text())
    identities=json.loads((paths['g2_baseline_run']/'score_identities.json').read_text());scales=json.loads((paths['g3_adaptive_run']/'train_gap_scales.json').read_text())
    specs=specifications(g3['fixed_G2_interior_reference']['settings'],scales)
    run=Run(ROOT,'g4_development_factory_preflight',dict(development_only=True,methods=specs),dict(source_metrics_sha256=digest(paths['g2_baseline_run']/'metrics.json')))
    print(run.id,flush=True);references={}
    for folder in paths.values():
        for r in csv.DictReader((folder/'per_query.csv').open()):references[r['split'],r['method'],r['query_image_id']]=r
    alias={'fixed_T_best':g2['best_temporal_only']['method'],'fixed_blend_best':g3['fixed_G2_interior_reference']['method'],
        'velocity08_L9':'temporal_L9_v0.8_lambda1','velocity10_L9':'temporal_L9_v1.0_lambda1'}
    for length in [3,5,9]:alias[f'full_velocity_T_L{length}']=f'temporal_L{length}_v0.8,1.0,1.2_lambda1'
    pipeline=joblib.load(paths['g3_smr_run']/'smr_pipeline.pkl');verified=[]
    for role in ['train','validation']:
        scores={}
        for name in ['cosplace','eigenplaces','dinov2']:
            p=paths['g2_baseline_run']/f'{role}_{name}_scores.npy';assert digest(p)==identities[f'{role}_{name}']['scores_sha256'];scores[name]=np.load(p)
        ids=identities[f'{role}_cosplace']
        for spec in specs:
            if spec['name']=='reverse_velocity_L9':continue # Predeclared new negative control, no old result reference.
            method=Method(ROOT,spec,pipeline);matched=0
            for i,q in enumerate(ids['query_ids']):
                rank,_=method.step({name:v[i] for name,v in scores.items()})
                name=alias.get(spec['name'],spec['name']);reference=references[role,name,q]
                actual='' if rank[0]<0 else ids['gallery_ids'][rank[0]]
                expected=reference.get('top1_image_id',reference.get('top1_gallery_image_id'))
                assert actual==expected,(role,name,q,actual,expected);matched+=1
            verified.append(dict(split=role,method=spec['name'],matched_top1_predictions=matched))
    run.write('metrics.json',dict(role='development deployment-factory replay only',verified=verified,total_predictions=sum(r['matched_top1_predictions'] for r in verified)))
    run.write('checks.json',dict(passed=True,all_23_existing_methods_two_roles_exact_top1=True,independent_unopened=True))
    with (run.path/'per_query.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(verified[0]));w.writeheader();w.writerows(verified)
    (run.path/'interpretation.md').write_text('Common method factory exactly reproduces all prior G2/G3/SMR development Top1 predictions, including rejection sentinels. This is cached accuracy replay, not latency. Reverse velocity is a predeclared negative control tested by causal unit invariants; no independent result read.\n')
    update_state(ROOT,g4_factory_preflight_run=run.id,latest_run_id=run.id)
    print(json.dumps(dict(run=run.id,predictions=sum(r['matched_top1_predictions'] for r in verified))),flush=True)

if __name__=='__main__':main()
