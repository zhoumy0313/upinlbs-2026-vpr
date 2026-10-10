#!/usr/bin/env python3
"""Real batch1 baseline latency on 64 evenly spaced validation images, 3 passes."""
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
from vpr_research.datasets import encoder_records, file_digest
from vpr_research.encoders.frozen import create_encoder
from vpr_research.retrieval import ExactCosineIndex


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--run-dir",type=Path,required=True)
    args=parser.parse_args()
    rows=encoder_records(args.manifest,ROOT,{"validation"})
    selected=[rows[i] for i in np.linspace(0,len(rows)-1,64,dtype=int)]
    device="cuda" if torch.cuda.is_available() else "cpu"
    def synchronize():
        if device=="cuda":torch.cuda.synchronize()
    results={"scope":"development baseline timing sample, not final full-set timing", "device":device,
             "batch_size":1,"warmup_queries_per_model":20,"passes":3,"queries_per_pass":64,
             "gallery_normalization_and_loading_outside_query_timer":True,
             "times_include":"warm filesystem decode, RGB, preprocess, real forward, D2H, exact cosine scores and top10 stable ranking",
             "times_exclude":"initial checkpoint load, gallery building, image-hash audit, disk-cold startup",
             "cached_query_descriptors_used_for_timing":False,"models":{}}
    measurements=[]
    for method in ["cosplace","dinov2"]:
        gallery,ids,fp=load_descriptors(args.run_dir/method,args.manifest,"gallery")
        queries,qids,_=load_descriptors(args.run_dir/method,args.manifest,"validation")
        reference=ExactCosineIndex(gallery)
        encoder=create_encoder(method,device)
        assert encoder.fingerprint()["model_state_sha256"]==fp["model"]["model_state_sha256"]
        def query(row):
            synchronize();t0=time.perf_counter_ns()
            with Image.open(row["path"]) as image:
                image.load();rgb=image.convert("RGB")
            t1=time.perf_counter_ns()
            descriptor=encoder.encode([rgb])
            synchronize();t2=time.perf_counter_ns()
            scores,ranks=reference.search(descriptor)
            t3=time.perf_counter_ns()
            return descriptor,ranks,{"decode_ms":(t1-t0)/1e6,"encoder_with_preprocess_ms":(t2-t1)/1e6,
                                     "retrieval_ms":(t3-t2)/1e6,"total_ms":(t3-t0)/1e6}
        for row in selected[:20]:query(row)
        if device=="cuda":torch.cuda.reset_peak_memory_stats()
        rows_for_method=[]
        for repeat in range(3):
            for row in selected:
                descriptor,ranks,elapsed=query(row)
                cached=queries[qids.index(row["image_id"]):qids.index(row["image_id"])+1]
                np.testing.assert_allclose(descriptor,cached,atol=1e-6,rtol=1e-6)
                np.testing.assert_array_equal(ranks,reference.search(cached)[1])
                entry={"method":method,"pass":repeat,"image_id":row["image_id"],**elapsed}
                measurements.append(entry);rows_for_method.append(entry)
        values=np.array([r["total_ms"] for r in rows_for_method])
        results["models"][method]={"n_measured":len(values),"mean_ms":float(values.mean()),
            "median_ms":float(np.median(values)),"p95_ms":float(np.percentile(values,95)),
            "component_mean_ms":{key:float(np.mean([r[key] for r in rows_for_method]))
                                  for key in ["decode_ms","encoder_with_preprocess_ms","retrieval_ms"]},
            "peak_torch_cuda_allocated_bytes":torch.cuda.max_memory_allocated() if device=="cuda" else None,
            "peak_torch_cuda_reserved_bytes":torch.cuda.max_memory_reserved() if device=="cuda" else None,
            "real_forward_outputs_match_cached_reference":True}
        del encoder
        if device=="cuda":torch.cuda.empty_cache()
    with (args.run_dir/"dev_latency_per_query.csv").open("x",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(measurements[0]));writer.writeheader();writer.writerows(measurements)
    with (args.run_dir/"dev_latency.json").open("x") as stream:json.dump(results,stream,indent=2)
    print(json.dumps(results,indent=2))


if __name__=="__main__":main()
