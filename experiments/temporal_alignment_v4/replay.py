"""Recompute published query-ledger metrics or replay local frozen descriptors."""
import csv,json,sys
import numpy as np
from runtime import *
from evaluation import audit_csv
def main():
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());results=[]
    for field in ['g2_run','g3_run','g4_run']:
        folder=ROOT/'outputs_v4'/s[field];metrics=json.loads((folder/'raw_metrics.json').read_text())['results'];audit=audit_csv(folder/'per_query.csv',metrics);results.append(dict(stage=field,run_id=s[field],**audit))
    if '--cached' in sys.argv:
        from features import with_scores
        from algorithms import predict
        for feature_run,seq,hzs,fields in [(s['development_feature_run'],'freiburg2_pioneer_slam',[1,3,5],['g2_run','g3_run']),(s['g4_run'],'freiburg3_long_office_household',[5],['g4_run'])]:
            grid=json.loads((ROOT/'configs/v4/search_grid.yaml').read_text());chosen=json.loads((ROOT/'configs/v4/selected_methods.json').read_text());methoddict={x['name']:x for x in grid['baselines']+grid['candidates']}
            for field in fields:
                folder=ROOT/'outputs_v4'/s[field];archive=np.load(folder/'all_top10_local.npz')
                for hz in hzs:
                    d=with_scores(seq,hz,ROOT/'outputs_v4'/feature_run)
                    for key in archive.files:
                        prefix=str(hz)+'_';name=key[len(prefix):] if key.startswith(prefix) else key
                        if field!='g4_run' and not key.startswith(prefix):continue
                        p,_=predict(d,methoddict[name]);assert np.array_equal(p,archive[key]),(seq,hz,key)
        results.append(dict(cached_replay='all stored top10 predictions exactly match frozen methods/descriptors, no model/test retuning',passed=True))
    print(json.dumps(dict(passed=True,results=results),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
