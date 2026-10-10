#!/usr/bin/env python3
"""Validate scalar decisions against batch policies on real cached dev rows."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import cosine_scores,score_features
from vpr_research.policies import ScorePolicy
from vpr_research.retrieval import ExactCosineIndex


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--feature-run",type=Path,required=True)
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    args=parser.parse_args()
    q,ids,_=load_descriptors(args.feature_run/"cosplace",args.manifest,"validation")
    db,_,_=load_descriptors(args.feature_run/"cosplace",args.manifest,"gallery")
    index=ExactCosineIndex(db)
    batch=score_features(cosine_scores(q,db))
    scalar=np.concatenate([score_features(index.scores(row[None,:])) for row in q])
    policies=json.loads((args.run_dir/"gate_development/policies.json").read_text())["policies"]
    checks={}
    for name,spec in policies.items():
        _,expected=ScorePolicy(spec).decide(batch)
        policy=ScorePolicy(spec)
        observed=np.array([policy.decide(row[None,:])[1][0] for row in scalar])
        different=np.flatnonzero(expected!=observed)
        checks[name]={"differences":int(len(different)),"query_ids":[ids[i] for i in different]}
    result={"scope":"cached numerical contract check; not model latency or final-test evidence",
            "maximum_feature_difference":float(abs(batch-scalar).max()),"policies":checks,
            "total_decision_differences":sum(x["differences"] for x in checks.values())}
    with (args.run_dir/"numerical_contract_probe.json").open("x") as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!="policies"},indent=2))
    if result["total_decision_differences"]:raise ValueError("Scalar and batch routing decisions differ; do not freeze")


if __name__=="__main__":main()
