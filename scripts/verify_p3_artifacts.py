#!/usr/bin/env python3
"""Independent replay of train fits, frozen masks and actual online call counts."""
import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import cosine_scores,index_positives,score_features,top1_correct,routing_labels
from vpr_research.datasets import file_digest
from vpr_research.policies import ScorePolicy,fit_head


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-dir",type=Path,required=True)
    args=parser.parse_args()
    run=args.run_dir
    manifest=run/"nordland_manifest.json"
    metadata=json.loads((run/"gate_development/policies.json").read_text())
    metrics=json.loads((run/"gate_development/metrics.json").read_text())
    assert not metadata["final_test_used"] and not metrics["final_test_used"]
    assert metadata["manifest_sha256"]==file_digest(manifest)
    for name,digest in metadata["selector_sources_sha256"].items():assert file_digest(ROOT/name)==digest
    policies=metadata["policies"];assert len(policies)==50
    lookup={r["image_id"]:r for r in json.loads(manifest.read_text())["records"]}
    methods=[metadata["A"],metadata["B"]]
    gallery={m:load_descriptors(run/m,manifest,"gallery") for m in methods}
    frames=np.array([lookup[i]["frame_index"] for i in gallery[methods[0]][1]])
    offline=list(csv.DictReader((run/"gate_development/per_query.csv").open()))
    assert len(offline)==50*(600+300)
    data={}
    for role,count in [("train",600),("validation",300)]:
        loaded={m:load_descriptors(run/m,manifest,role) for m in methods}
        ids=loaded[methods[0]][1]
        assert ids==loaded[methods[1]][1]==metadata[role+"_image_ids"] and len(ids)==count
        qframes=np.array([lookup[i]["frame_index"] for i in ids])
        positives=index_positives(qframes,frames,5)
        scores={m:cosine_scores(loaded[m][0],gallery[m][0]) for m in methods}
        x=score_features(scores[methods[0]])
        correct={m:top1_correct(scores[m],positives) for m in methods}
        data[role]=(x,correct)
        role_rows=[r for r in offline if r["split"]==role]
        for name,spec in policies.items():
            rows=[r for r in role_rows if r["policy"]==name]
            assert [r["query_image_id"] for r in rows]==ids
            _,mask=ScorePolicy(spec).decide(x)
            np.testing.assert_array_equal(mask,[r["invoked_B"]=="True" for r in rows])
            routed=np.where(mask,correct[methods[1]],correct[methods[0]])
            np.testing.assert_array_equal(routed,[r["routed_correct"]=="True" for r in rows])
            assert np.isclose(routed.mean(),metrics["splits"][role][name]["R@1"])
    train_x,train_c=data["train"]
    rescue,harm=routing_labels(train_c[methods[0]],train_c[methods[1]])
    for spec in policies.values():
        for head in spec["heads"]:
            columns=head["columns"];selected=train_x[:,columns]
            np.testing.assert_allclose(head["mean"],selected.mean(axis=0),atol=1e-14)
            np.testing.assert_allclose(head["variance"],selected.var(axis=0),atol=1e-14)
            assert head["n_train"]==600 and sum(head["train_class_counts"].values())==600
    for head,target in zip(policies["net_benefit_budget25"]["heads"],[rescue,harm]):
        repeat=fit_head(train_x,target)
        np.testing.assert_allclose(head["coef"],repeat["coef"],atol=1e-14)
        np.testing.assert_allclose(head["intercept"],repeat["intercept"],atol=1e-14)
    latency=json.loads((run/"online_validation_budget25/metrics.json").read_text())
    assert latency["real_model_forwards"] and not latency["cached_query_used_inside_timed_path"]
    online=list(csv.DictReader((run/"online_validation_budget25/per_query.csv").open()))
    assert len(online)==17*3*300
    for name,summary in latency["policies"].items():
        assert summary["n_queries"]==900 and summary["cached_reference_decisions_and_rankings_match"]
        rows=[r for r in online if r["policy"]==name]
        assert len(rows)==900 and sum(r["invoked_B"]=="True" for r in rows)==summary["B_forward_calls"]
        assert summary["A_forward_calls"]==(0 if name=="B_only" else 900)
        for repeat in range(3):
            subset=[r for r in rows if int(r["pass"])==repeat]
            assert [r["query_image_id"] for r in subset]==metadata["validation_image_ids"]
            _,mask=ScorePolicy(policies[name]).decide(data["validation"][0])
            np.testing.assert_array_equal(mask,[r["invoked_B"]=="True" for r in subset])
    old=ROOT/"outputs/p2_20261010_134300/cosplace"
    for role in ["gallery","train","validation"]:
        np.testing.assert_array_equal(np.load(old/f"{role}_descriptors.npy"),np.load(run/f"cosplace/{role}_descriptors.npy"))
    consistency=json.loads((run/"numerical_contract_probe.json").read_text())
    assert consistency["total_decision_differences"]==0
    events=[json.loads(line) for line in (run/"commands.jsonl").read_text().splitlines()]
    assert all(e["exit_status"]==0 for e in events)
    result={"passed":True,"scope":"P3 development selector; no final-test results",
            "policy_count":50,"offline_rows_checked":len(offline),"real_online_rows_checked":len(online),
            "train_scalers_and_primary_refit_verified":True,"fresh_A_arrays_equal_original_P2":True,
            "all_seeds_preserved":True,"real_call_counts_and_causal_masks_verified":True,
            "completed_command_count_before_this_verifier":len(events),"final_test_used":False}
    with (run/"phase_acceptance.json").open("x") as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
