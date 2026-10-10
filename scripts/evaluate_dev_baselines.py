#!/usr/bin/env python3
"""Closed-set development evaluation; labels stay in this evaluator only."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import roc_auc_score
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "src"))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import (cosine_scores, index_positives, l2_normalize, ranking,
                               recall_at_k, score_features, top1_correct)
from vpr_research.datasets import file_digest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument("--second-method",choices=["dinov2","eigenplaces"],default="dinov2")
    args=parser.parse_args()
    config=yaml.safe_load((ROOT/"configs/protocol.yaml").read_text())
    records=json.loads(args.manifest.read_text())["records"]
    lookup={r["image_id"]:r for r in records}
    out=args.run_dir/"dev_baselines"
    out.mkdir()
    radius=config["data"]["nordland"]["positive_radius_frames_primary"]
    gallery={}
    for method in ["cosplace",args.second_method]:
        gallery[method]=load_descriptors(args.run_dir/method,args.manifest,"gallery")
    assert gallery["cosplace"][1]==gallery[args.second_method][1]
    db_ids=gallery["cosplace"][1]
    db_frames=np.array([lookup[i]["frame_index"] for i in db_ids])
    np.testing.assert_array_equal(db_frames,np.arange(1,1751))
    summary={"dataset":"Nordland-Part-2020","primary_positive_radius_frames":radius,
             "development_only":True,"B_method":args.second_method,"final_test_metrics_computed":False,"splits":{}}
    for role,count in [("train",600),("validation",300)]:
        models={}
        for method in ["cosplace",args.second_method]:
            q,ids,fp=load_descriptors(args.run_dir/method,args.manifest,role)
            frames=np.array([lookup[i]["frame_index"] for i in ids])
            expected=config["data"]["nordland"]["query_"+role]
            np.testing.assert_array_equal(frames,np.arange(expected[0],expected[1]+1))
            assert len(q)==count and all(lookup[i]["split"]==role for i in ids)
            s=cosine_scores(q,gallery[method][0])
            p=index_positives(frames,db_frames,radius)
            ranks=ranking(s,10)
            correct=top1_correct(s,p)
            # Independent full-distance formula cross-check on 32 real queries.
            qn,dn=l2_normalize(q[:32]),l2_normalize(gallery[method][0])
            dist=((qn[:,None,:]-dn[None,:,:])**2).sum(axis=2)
            np.testing.assert_array_equal(np.argsort(dist,axis=1,kind="stable")[:,:10],ranks[:32])
            np.save(out/f"{role}_{method}_scores.npy",s)
            models[method]={"ids":ids,"frames":frames,"scores":s,"ranks":ranks,"correct":correct,
                            "recall":recall_at_k(s,p),"fingerprint_sha256":file_digest(args.run_dir/method/"fingerprint.json")}
        a,b=models["cosplace"],models[args.second_method]
        assert a["ids"]==b["ids"]
        features=score_features(a["scores"])
        groups=np.array(["both_right" if x and y else "A_wrong_B_right" if y else
                         "A_right_B_wrong" if x else "both_wrong" for x,y in zip(a["correct"],b["correct"])])
        np.save(out/f"{role}_A_only_features.npy",features)
        (out/f"{role}_query_image_ids.json").write_text(json.dumps(a["ids"],indent=2))
        counts={key:int((groups==key).sum()) for key in ["both_right","A_wrong_B_right","A_right_B_wrong","both_wrong"]}
        assert sum(counts.values())==count
        assert np.isclose((b["correct"].mean()-a["correct"].mean())*100,
                          (counts["A_wrong_B_right"]-counts["A_right_B_wrong"])*100/count)
        feature_audit={}
        for j,name in enumerate(config["gate"]["features"]):
            feature_audit[name]={"mean_by_outcome":{key:float(features[groups==key,j].mean())
                                                   if (groups==key).any() else None for key in counts},
                                 "rescue_auc_raw_feature":float(roc_auc_score(groups=="A_wrong_B_right",features[:,j]))
                                 if len(np.unique(groups=="A_wrong_B_right"))==2 else None,
                                 "note":"Exploratory development-only univariate discrimination; no fitted gate or selected threshold."}
        with (out/f"{role}_per_query.csv").open("x",newline="") as stream:
            names=["query_image_id","split","frame_index","A_correct","B_correct","outcome",
                   "A_top1_image_id","B_top1_image_id","A_top1_abs_frame_error","B_top1_abs_frame_error"]
            names+=config["gate"]["features"]+["A_top10_image_ids","B_top10_image_ids"]
            writer=csv.DictWriter(stream,fieldnames=names);writer.writeheader()
            for i,image_id in enumerate(a["ids"]):
                row=dict(zip(names[:10],[image_id,role,int(a["frames"][i]),bool(a["correct"][i]),bool(b["correct"][i]),
                     groups[i],db_ids[a["ranks"][i,0]],db_ids[b["ranks"][i,0]],
                     int(abs(db_frames[a["ranks"][i,0]]-a["frames"][i])),int(abs(db_frames[b["ranks"][i,0]]-a["frames"][i]))]))
                row.update(dict(zip(config["gate"]["features"],map(float,features[i]))))
                row.update({label+"_top10_image_ids":json.dumps([db_ids[k] for k in model["ranks"][i]])
                            for label,model in [("A",a),("B",b)]})
                writer.writerow(row)
        summary["splits"][role]={"n_queries":count,"n_gallery":len(db_ids),
            "A_CosPlace":a["recall"],"B_DINOv2" if args.second_method=="dinov2" else "B_EigenPlaces":b["recall"],"complementarity_counts":counts,
            "oracle_R1_DIAGNOSTIC_ONLY":float((a["correct"]|b["correct"]).mean()),
            "B_minus_A_R1_percentage_points":100*float(b["correct"].mean()-a["correct"].mean()),
            "potential_rescue_percentage_points":100*counts["A_wrong_B_right"]/count,
            "feature_audit":feature_audit,"source_fingerprints":{m:v["fingerprint_sha256"] for m,v in models.items()},
            "cosine_vs_independent_L2_top10_real_queries_checked":32}
    (out/"metrics.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:{n:v for n,v in x.items() if n!="feature_audit"} for k,x in summary["splits"].items()},indent=2))


if __name__=="__main__":
    main()
