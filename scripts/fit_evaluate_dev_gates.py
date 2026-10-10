#!/usr/bin/env python3
"""Only fixed train fits and validation thresholds; preserve every routing result."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from sklearn.metrics import roc_auc_score
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import (cosine_scores,index_positives,ranking,recall_at_k,routing_audit,
                              routing_labels,route_scores,score_features,top1_correct,validation_threshold)
from vpr_research.datasets import file_digest
from vpr_research.policies import ScorePolicy,export_threshold,fit_head


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--feature-run",type=Path,required=True)
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--second-method",choices=["dinov2","eigenplaces"],default="dinov2")
    args=parser.parse_args()
    config=yaml.safe_load((ROOT/"configs/protocol.yaml").read_text())
    lookup={r["image_id"]:r for r in json.loads(args.manifest.read_text())["records"]}
    gallery={m:load_descriptors(args.feature_run/m,args.manifest,"gallery") for m in ["cosplace",args.second_method]}
    assert gallery["cosplace"][1]==gallery[args.second_method][1]
    db_frames=np.array([lookup[i]["frame_index"] for i in gallery["cosplace"][1]])
    data={}
    for role in ["train","validation"]:
        models={}
        for method in gallery:
            features,ids,fp=load_descriptors(args.feature_run/method,args.manifest,role)
            assert all(lookup[i]["split"]==role for i in ids)
            frames=np.array([lookup[i]["frame_index"] for i in ids])
            expected=config["data"]["nordland"]["query_"+role]
            np.testing.assert_array_equal(frames,np.arange(expected[0],expected[1]+1))
            scores=cosine_scores(features,gallery[method][0])
            positives=index_positives(frames,db_frames,config["data"]["nordland"]["positive_radius_frames_primary"])
            models[method]={"scores":scores,"correct":top1_correct(scores,positives),"ids":ids,"fingerprint_sha256":file_digest(args.feature_run/method/"fingerprint.json")}
        a,b=models["cosplace"],models[args.second_method]
        assert a["ids"]==b["ids"]
        data[role]={"A":a,"B":b,"positives":positives,"features":score_features(a["scores"])}
    train,val=data["train"],data["validation"]
    rescue,harm=routing_labels(train["A"]["correct"],train["B"]["correct"])
    x=train["features"];c=config["gate"]["C"];max_iter=config["gate"]["max_iter"]
    positive=fit_head(x,rescue,c=c,max_iter=max_iter)
    negative=fit_head(x,harm,c=c,max_iter=max_iter)
    error=fit_head(x,(~train["A"]["correct"]).astype(int),c=c,max_iter=max_iter)
    correct=fit_head(x,train["A"]["correct"].astype(int),c=c,max_iter=max_iter)
    bases={
        "net_benefit":{"kind":"net_benefit","heads":[positive,negative]},
        "trained_A_error":{"kind":"error_two_head","heads":[error,correct]},
        "A_error_single_head":{"kind":"error_single_head","heads":[error]},
        "gap":{"kind":"gap","heads":[]},
        "rescue_only":{"kind":"rescue_only","heads":[positive]},
        "net_benefit_no_std":{"kind":"net_benefit_no_std","heads":[fit_head(x,rescue,(0,1,2,3),c,max_iter=max_iter),fit_head(x,harm,(0,1,2,3),c,max_iter=max_iter)]}}
    policies={"A_only":{"kind":"always_A","threshold":export_threshold(0),"heads":[]},
              "B_only":{"kind":"always_B","threshold":export_threshold(0),"heads":[]}}
    validation_masks={}
    for budget in config["gate"]["validation_budgets"]:
        suffix=f"budget{round(budget*100):02d}"
        for name,base in bases.items():
            spec={**base,"budget":budget,"seed":0,"threshold":export_threshold(0)}
            values=ScorePolicy(spec).score(val["features"])
            positive_only=base["kind"] in {"net_benefit","net_benefit_no_std"}
            spec["threshold"]=export_threshold(validation_threshold(values,budget,positive_only))
            key=name+"_"+suffix
            policies[key]=spec
            validation_masks[key]=ScorePolicy(spec).decide(val["features"])[1]
        matched=float(validation_masks["net_benefit_"+suffix].mean())
        for family,target in [("random_budget",budget),("random_matched_net",matched)]:
            for seed in config["random_controls"]["seeds"]:
                spec={"kind":"random","heads":[],"budget":budget,"validation_target_fraction":target,"seed":seed,"threshold":export_threshold(0)}
                values=ScorePolicy(spec).score(val["features"])
                # Exact integer matching avoids floor((n/N)*N) floating-point loss.
                if family=="random_matched_net":
                    n=int(validation_masks["net_benefit_"+suffix].sum())
                    threshold=float("inf") if n==0 else float(np.sort(values)[-(n+1)])
                    spec["validation_matched_invocations"]=n
                else:threshold=validation_threshold(values,target,False)
                spec["threshold"]=export_threshold(threshold)
                if family=="random_matched_net":
                    assert int(ScorePolicy(spec).decide(val["features"])[1].sum())==n
                policies[f"{family}_{suffix}_seed{seed}"]=spec
        # The matched two-head error control has the same ranking as one-head error.
        np.testing.assert_array_equal(validation_masks["trained_A_error_"+suffix],validation_masks["A_error_single_head_"+suffix])
    out=args.run_dir/"gate_development";out.mkdir()
    metadata={"A":"cosplace","B":args.second_method,"feature_run":str(args.feature_run.resolve()),
              "manifest_sha256":file_digest(args.manifest),"protocol_sha256":file_digest(ROOT/"configs/protocol.yaml"),
              "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
              "selector_sources_sha256":{p:file_digest(ROOT/p) for p in ["src/vpr_research/policies.py","scripts/fit_evaluate_dev_gates.py","src/vpr_research/core.py"]},
              "train_image_ids":train["A"]["ids"],"validation_image_ids":val["A"]["ids"],
              "feature_names":config["gate"]["features"],"fit_split":"train_only","threshold_split":"validation_only",
              "heads_capacity_note":"Primary error control fits error/correct heads with the same architecture and regularization as rescue/harm. Complementary targets induce the same ordering as a single error head; both variants reported.",
              "no_std_ablation_columns":[0,1,2,3],"final_test_used":False,
              "policies":policies}
    with (out/"policies.json").open("x") as stream:json.dump(metadata,stream,indent=2,allow_nan=False)
    rows=[];summaries={}
    for role,split in data.items():
        a,b=split["A"],split["B"];summaries[role]={}
        for name,spec in policies.items():
            gate_score,mask=ScorePolicy(spec).decide(split["features"])
            routed=route_scores(a["scores"],b["scores"],mask)
            audit=routing_audit(a["correct"],b["correct"],mask)
            metric={**recall_at_k(routed,split["positives"]),**audit,"kind":spec["kind"],"budget":spec.get("budget")}
            assert np.isclose(metric["R@1"]-a["correct"].mean(),metric["net_gain_percentage_points"]/100,atol=1e-14)
            summaries[role][name]=metric
            top=ranking(routed,1)[:,0]
            for i,image_id in enumerate(a["ids"]):
                rows.append({"split":role,"policy":name,"query_image_id":image_id,"gate_score":float(gate_score[i]),
                    "invoked_B":bool(mask[i]),"A_correct":bool(a["correct"][i]),"B_correct":bool(b["correct"][i]),
                    "routed_correct":bool(np.where(mask,b["correct"],a["correct"])[i]),"top1_image_id":gallery["cosplace"][1][top[i]]})
        mask=(~a["correct"]&b["correct"])
        summaries[role]["oracle_DIAGNOSTIC_ONLY"]={**recall_at_k(route_scores(a["scores"],b["scores"],mask),split["positives"]),**routing_audit(a["correct"],b["correct"],mask),"deployable":False}
    with (out/"per_query.csv").open("x",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    random_summary={}
    for role in summaries:
        random_summary[role]={}
        for budget in config["gate"]["validation_budgets"]:
            for family in ["random_budget","random_matched_net"]:
                prefix=f"{family}_budget{round(budget*100):02d}"
                values=[summaries[role][prefix+f"_seed{s}"] for s in config["random_controls"]["seeds"]]
                random_summary[role][prefix]={key:{"mean":float(np.mean([v[key] for v in values])),"std_population":float(np.std([v[key] for v in values],ddof=0))} for key in ["R@1","invocation_fraction","rescues","harms","net_gain_percentage_points"]}
    result={"development_only":True,"encoder_training":False,"small_selector_training":True,"final_test_used":False,
            "source_fingerprints":{role:{k:d["fingerprint_sha256"] for k,d in [("A",x["A"]),("B",x["B"])]} for role,x in data.items()},
            "splits":summaries,"random_all_seeds_summary":random_summary,
            "SU_status":"not implemented: official code/numerical convention unverified"}
    with (out/"metrics.json").open("x") as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({n:v for n,v in summaries["validation"].items() if "seed" not in n},indent=2))


if __name__=="__main__":main()
