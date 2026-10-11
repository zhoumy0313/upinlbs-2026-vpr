import csv,json
import numpy as np
from runtime import *
from features import encode,with_scores
from algorithms import predict
from evaluation import evaluate,audit_csv,FIELDS
def verify(freeze):
    for p,h in freeze['file_sha256'].items():assert sha(ROOT/p)==h,p
def main():
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());assert not s['independent_retrieval_opened'],'TEST ALREADY OPENED; no repeat blind evaluation'
    freeze=json.loads((ROOT/s['freeze_folder']/'freeze.json').read_text());verify(freeze);config=freeze['evaluation']
    run=Run('g4_independent',dict(freeze_sha256=sha(ROOT/s['freeze_folder']/'freeze.json'),first_and_only_blind_retrieval=True,methods=len(config['all_test_methods']),test='freiburg3_long_office_household'))
    # Mark opened BEFORE extraction/evaluation to retain honest failed-first-run history.
    s.update(independent_retrieval_opened=True,first_independent_test_run=run.id,test_state='opened_run_in_progress');write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    cost=encode('freiburg3_long_office_household',[5],run);assert json.loads((run.path/'model_identity.json').read_text())==freeze['model_identity'];d=with_scores('freiburg3_long_office_household',5,run.path);a,_=predict(d,config['all_test_methods'][0]);metrics=[];preds={}
    with (run.path/'per_query.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for spec in config['all_test_methods']:
            p,meta=predict(d,spec);metrics.extend(evaluate(d,spec,p,meta,writer,a));preds[spec['name']]=p
    np.savez_compressed(run.path/'all_top10_local.npz',**preds);audit=audit_csv(run.path/'per_query.csv',metrics);write(run.path/'independent_numeric_audit.json',audit)
    selected=json.loads((ROOT/'configs/v4/selected_methods.json').read_text());pc={str(r):next(m['correct1'] for m in metrics if m['method']==selected['proposed']['name'] and m['radius_m']==r) for r in [.25,.5]};envelope={str(r):max(m['correct1'] for m in metrics if m['kind']!='time_P' and m['radius_m']==r) for r in [.25,.5]};testgate=all(pc[str(r)]>envelope[str(r)] for r in [.25,.5]);claim=bool(testgate and selected['development_positive_gate'])
    result=dict(run_id=run.id,results=metrics,blind_evaluations=1,proposed_correct1=pc,baseline_envelope_correct1=envelope,test_positive_gate=testgate,development_positive_gate=selected['development_positive_gate'],positive_method_claim_supported=claim,offline_feature_cost=cost,freeze_sha256=sha(ROOT/s['freeze_folder']/'freeze.json'))
    write(ROOT/'docs/research_v4/INDEPENDENT_RESULTS.json',result)
    s.update(g4_run=run.id,test_state='single_blind_run_complete',positive_method_claim=claim,current_stage='G5',test_positive_gate=testgate);write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    (ROOT/'docs/research_v4/G4_ACCEPTANCE.md').write_text(f'# G4 — one independent test complete\n\nImmutable source/model/data/protocol/settings freeze preceded the first Long Office retrieval. All {len(config["all_test_methods"])} frozen methods on the same 168 queries/order; primary closed N=48, strict N=20, wider N=89; all open/no-positive counts and no-rejection false accepts explicit. No method/threshold/sampling/protocol was changed from test scores. Candidate correct@1 {pc}, mature/simple baseline envelope {envelope}; strict-both-radii test gate={testgate}, combined developer+test claim gate={claim}. Full query and negative results retained, independent numeric CSV audit passes. Small, correlated closed-set N limits conclusions; no SOTA/generalization claim. No second blind execution is permitted. Next: frozen real batch-one timing and batch-size numerical accuracy audit, not method selection.\n')
    run.finish(result);run.checkpoint('G4 single frozen independent test with all negative results')
    print(json.dumps(dict(pc=pc,envelope=envelope,positive_claim=claim)),flush=True)
if __name__=='__main__':main()
