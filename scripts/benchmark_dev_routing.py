#!/usr/bin/env python3
"""Real full validation passes; only call B after the A-only gate decision."""
import argparse
import csv
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import ranking,score_features
from vpr_research.datasets import encoder_records,file_digest
from vpr_research.encoders.frozen import create_encoder
from vpr_research.online import ConditionalRetriever
from vpr_research.policies import ScorePolicy
from vpr_research.retrieval import ExactCosineIndex


class CountEncoder:
    def __init__(self,encoder):self.encoder=encoder;self.calls=0
    def encode(self,images):self.calls+=1;return self.encoder.encode(images)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--feature-run",type=Path,required=True)
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--budget",type=int,choices=[10,25,50],default=25)
    args=parser.parse_args()
    metadata=json.loads((args.run_dir/"gate_development/policies.json").read_text())
    methods=["cosplace",metadata["B"]]
    gallery={m:load_descriptors(args.feature_run/m,args.manifest,"gallery") for m in methods}
    query={m:load_descriptors(args.feature_run/m,args.manifest,"validation") for m in methods}
    assert gallery[methods[0]][1]==gallery[methods[1]][1] and query[methods[0]][1]==query[methods[1]][1]
    rows=encoder_records(args.manifest,ROOT,{"validation"})
    assert len(rows)==300 and [r["image_id"] for r in rows]==query[methods[0]][1]
    indices={m:ExactCosineIndex(gallery[m][0]) for m in methods}
    references={m:indices[m].scores(query[m][0]) for m in methods}
    a_features=score_features(references[methods[0]])
    suffix=f"budget{args.budget:02d}"
    names=["A_only","B_only"]
    names += [f"{m}_{suffix}" for m in ["net_benefit","trained_A_error","gap","rescue_only","net_benefit_no_std"]]
    names += [f"{family}_{suffix}_seed{s}" for family in ["random_budget","random_matched_net"] for s in range(5)]
    out=args.run_dir/f"online_validation_budget{args.budget:02d}";out.mkdir()
    device="cuda" if torch.cuda.is_available() else "cpu"
    measurements=[];summaries={}
    def synchronize():
        if device=="cuda":torch.cuda.synchronize()
    for name in names:
        spec=metadata["policies"][name]
        needed=[methods[0]] if name=="A_only" else [methods[1]] if name=="B_only" else methods
        encoders={}
        for m in needed:
            encoder=create_encoder(m,device)
            assert encoder.fingerprint()["model_state_sha256"]==gallery[m][2]["model"]["model_state_sha256"]
            encoders[m]=CountEncoder(encoder)
        policy=ScorePolicy(spec)
        pipeline=None if name in {"A_only","B_only"} else ConditionalRetriever(encoders[methods[0]],indices[methods[0]],encoders[methods[1]],indices[methods[1]],policy)
        def infer(row):
            synchronize();started=time.perf_counter_ns()
            with Image.open(row["path"]) as image:
                image.load();image=image.convert("RGB")
            decoded=time.perf_counter_ns()
            if pipeline is None:
                m=needed[0]
                scores,ranks=indices[m].search(encoders[m].encode([image]))
                result={"scores":scores,"ranks":ranks,"invoked_B":name=="B_only","gate_score":None}
            else:result=pipeline.infer(image)
            synchronize();finished=time.perf_counter_ns()
            return result,{"decode_ms":(decoded-started)/1e6,"pipeline_ms":(finished-decoded)/1e6,"total_ms":(finished-started)/1e6}
        for row in rows[:20]:infer(row)
        for encoder in encoders.values():encoder.calls=0
        if pipeline:pipeline.a_calls=pipeline.b_calls=0
        if device=="cuda":torch.cuda.reset_peak_memory_stats()
        entries=[]
        for repeat in range(3):
            policy.reset()
            _,expected_mask=ScorePolicy(spec).decide(a_features)
            for i,row in enumerate(rows):
                result,elapsed=infer(row)
                assert result["invoked_B"]==bool(expected_mask[i]),"Causal mask differs from frozen validation reference"
                m=methods[1] if result["invoked_B"] else methods[0]
                np.testing.assert_allclose(result["scores"],references[m][i:i+1],atol=1e-6,rtol=1e-6)
                np.testing.assert_array_equal(result["ranks"],ranking(references[m][i:i+1],10))
                entry={"policy":name,"pass":repeat,"query_image_id":row["image_id"],"invoked_B":result["invoked_B"],
                       "gate_score":result["gate_score"],"top1_image_id":gallery[m][1][result["ranks"][0,0]],**elapsed}
                entries.append(entry);measurements.append(entry)
        a_calls=encoders[methods[0]].calls if methods[0] in encoders else 0
        b_calls=encoders[methods[1]].calls if methods[1] in encoders else 0
        expected_b=int(sum(r["invoked_B"] for r in entries))
        assert b_calls==expected_b
        assert a_calls==(0 if name=="B_only" else 900)
        values=np.array([r["total_ms"] for r in entries])
        summaries[name]={"n_queries":900,"A_forward_calls":a_calls,"B_forward_calls":b_calls,
                         "B_invocation_fraction":b_calls/900,"mean_ms":float(values.mean()),
                         "median_ms":float(np.median(values)),"p95_ms":float(np.percentile(values,95)),
                         "peak_torch_cuda_allocated_bytes":torch.cuda.max_memory_allocated() if device=="cuda" else None,
                         "peak_torch_cuda_reserved_bytes":torch.cuda.max_memory_reserved() if device=="cuda" else None,
                         "resident_encoders":needed,"cached_reference_decisions_and_rankings_match":True}
        print(json.dumps({"completed_policy":name,**summaries[name]}),flush=True)
        # Release every reference to GPU models before measuring the next method.
        pipeline=None;encoders.clear();del encoder
        if device=="cuda":torch.cuda.empty_cache()
    with (out/"per_query.csv").open("x",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(measurements[0]));writer.writeheader();writer.writerows(measurements)
    summary={"scope":"development full validation only","device":device,"batch_size":1,"warmup_per_policy":20,
             "validation_queries":300,"repeated_full_passes":3,"target_budget_percent":args.budget,
             "policy_source_sha256":file_digest(args.run_dir/"gate_development/policies.json"),
             "real_model_forwards":True,"cached_query_used_inside_timed_path":False,
             "includes":"warm-file decode, RGB, preprocess, real selected encoders, exact global retrieval and gate",
             "excludes":"model/index loading, weight hashing, gallery building, reference checks, cold filesystem cost",
             "policies":summaries}
    with (out/"metrics.json").open("x") as stream:json.dump(summary,stream,indent=2,allow_nan=False)
    print(out/"metrics.json")


if __name__=="__main__":main()
