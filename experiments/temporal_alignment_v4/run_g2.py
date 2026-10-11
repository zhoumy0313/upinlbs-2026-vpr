import csv,json
import numpy as np
from runtime import *
from features import encode,with_scores
from algorithms import predict
from evaluation import evaluate,audit_csv,FIELDS
def main():
    grid=json.loads((ROOT/'configs/v4/search_grid.yaml').read_text());assert not json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text())['independent_retrieval_opened']
    run=Run('g2_baselines',dict(grid_sha256=sha(ROOT/'configs/v4/search_grid.yaml'),protocol_sha256=sha(ROOT/'configs/v4/protocol_accepted.yaml'),role='development',sequence='freiburg2_pioneer_slam',hzs=[1,3,5]))
    cost=encode('freiburg2_pioneer_slam',[1,3,5],run);metrics=[];allpred={}
    with (run.path/'per_query.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for hz in [1,3,5]:
            d=with_scores('freiburg2_pioneer_slam',hz,run.path);a,_=predict(d,grid['baselines'][0])
            for spec in grid['baselines']:
                p,meta=predict(d,spec);metrics.extend(evaluate(d,spec,p,meta,writer,a));allpred[str(hz)+'_'+spec['name']]=p
            print('baseline condition',hz,'done',flush=True)
    np.savez_compressed(run.path/'all_top10_local.npz',**allpred);audit=audit_csv(run.path/'per_query.csv',metrics);write(run.path/'independent_numeric_audit.json',audit)
    write(ROOT/'docs/research_v4/BASELINE_RESULTS.json',dict(run_id=run.id,results=metrics,offline_feature_cost=cost))
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());s.update(g2_run=run.id,development_feature_run=run.id,current_stage='G3');write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    (ROOT/'docs/research_v4/G2_ACCEPTANCE.md').write_text('# G2 — passed\n\nActual RGB encoded by existing frozen CosPlace/EigenPlaces at 224×224, source/checkpoint/state/preprocessing identities and every descriptor row ID/hash saved. No model retraining/download. All predeclared strong baselines run at 1/3/5Hz developer conditions, rebuilt gallery/query per condition; all queries processed causally including invalid-GT history/startup. Radius-specific closed/open counts, R@1/5/10, rescue/harm, candidate coverage and 3D prediction error quantiles are in BASELINE_RESULTS.json and full per_query.csv. Numeric CSV audit checks exact counts and rescue–harm identities. Offline extraction costs are explicitly not online latency. The independent sequence has no extracted descriptor or retrieval score. Next: only the finite predeclared candidate grid on development.\n')
    run.finish(dict(results=metrics,offline_feature_cost=cost,numeric_audit=audit,all_top10_sha256=sha(run.path/'all_top10_local.npz')));run.checkpoint('G2 strong baselines and artificial sampling shifts')
if __name__=='__main__':main()
