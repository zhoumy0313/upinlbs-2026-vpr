#!/usr/bin/env python3
"""Prospective final evaluation only after confirmation of an immutable package.

No fitting, model selection or test threshold calibration exists in this entry.
Labels are used only for evaluation after descriptors/decisions are computed.
"""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"scripts"))
from frozen_package import digest,validate_package
from vpr_research.core import cosine_scores,index_positives,ranking,recall_at_k,route_scores,routing_audit,score_features,top1_correct
from vpr_research.datasets import encoder_records
from vpr_research.encoders.frozen import create_encoder
from vpr_research.online import ConditionalRetriever
from vpr_research.policies import ScorePolicy
from vpr_research.retrieval import ExactCosineIndex


def write_json(path,value):
    with path.open("x") as stream:json.dump(value,stream,indent=2,allow_nan=False)


def write_csv(path,rows):
    with path.open("x",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


class CountEncoder:
    def __init__(self,encoder):self.encoder=encoder;self.calls=0
    def encode(self,images):self.calls+=1;return self.encoder.encode(images)


def make_encoder(method,package,device):
    source=package["models"][method]
    assert digest(ROOT/source["checkpoint"])==source["checkpoint_sha256"]
    encoder=create_encoder(method,device)
    fp=encoder.fingerprint()
    assert fp["model_state_sha256"]==package["model_state_sha256"][method]
    assert fp["eval_mode"] and fp["all_parameters_frozen"]
    return encoder,fp


def extract(manifest,config,output,package,device):
    rows={role:encoder_records(manifest,ROOT,{role},allow_final_test=True)
          for role in ["gallery",config["query_role"]]}
    assert len(rows["gallery"])==config["gallery"] and len(rows[config["query_role"]])==config["queries"]
    arrays={};metadata={}
    for method in ["cosplace","dinov2","eigenplaces"]:
        directory=output/method;directory.mkdir()
        encoder,fp=make_encoder(method,package,device)
        arrays[method]={};metadata[method]={"model":fp,"manifest_sha256":digest(manifest),"roles":{}}
        for role,records in rows.items():
            started=time.perf_counter();values=[]
            for i,row in enumerate(records):
                assert digest(row["path"])==row["sha256"]
                with Image.open(row["path"]) as image:values.append(encoder.encode([image]))
                if (i+1)%250==0:print(json.dumps({"extract":method,"role":role,"images":i+1}),flush=True)
            result=np.concatenate(values)
            assert result.dtype==np.float32 and result.shape==(len(records),encoder.dimension) and np.isfinite(result).all()
            np.testing.assert_allclose(np.linalg.norm(result,axis=1),1,atol=1e-5)
            target=directory/(role+"_descriptors.npy");np.save(target,result)
            ids=[r["image_id"] for r in records]
            write_json(directory/(role+"_image_ids.json"),ids)
            arrays[method][role]=(result,ids)
            metadata[method]["roles"][role]={"sha256":digest(target),"shape":list(result.shape),"array_bytes":result.nbytes,
                "offline_build_seconds":time.perf_counter()-started,"includes":"hash/decode/preprocess/real batch1 encoding/saving; not online latency"}
        write_json(directory/"fingerprint.json",metadata[method])
        del encoder
        if device=="cuda":torch.cuda.empty_cache()
    return arrays,rows


def accuracy(manifest,config,arrays,policies,second,output):
    lookup={r["image_id"]:r for r in json.loads(manifest.read_text())["records"]}
    role=config["query_role"];methods=["cosplace",second]
    db_ids=arrays["cosplace"]["gallery"][1];ids=arrays["cosplace"][role][1]
    assert all(arrays[m]["gallery"][1]==db_ids and arrays[m][role][1]==ids for m in methods)
    qframes=np.array([lookup[i]["frame_index"] for i in ids]);dframes=np.array([lookup[i]["frame_index"] for i in db_ids])
    scores={m:cosine_scores(arrays[m][role][0],arrays[m]["gallery"][0]) for m in methods}
    x=score_features(scores["cosplace"]);masks={n:ScorePolicy(s).decide(x) for n,s in policies.items()}
    all_metrics={};rows=[]
    for radius in [config["primary_radius"]]+config["sensitivity_radii"]:
        positives=index_positives(qframes,dframes,radius)
        a=top1_correct(scores["cosplace"],positives);b=top1_correct(scores[second],positives)
        summary={}
        for name,(gate_score,mask) in masks.items():
            routed=route_scores(scores["cosplace"],scores[second],mask)
            metric={**recall_at_k(routed,positives),**routing_audit(a,b,mask)}
            assert np.isclose(metric["R@1"]-a.mean(),metric["net_gain_percentage_points"]/100,atol=1e-14)
            summary[name]=metric
            if radius==config["primary_radius"]:
                top=ranking(routed,10)
                for i,image_id in enumerate(ids):
                    rows.append({"policy":name,"query_image_id":image_id,"gate_score":float(gate_score[i]),
                        "invoked_B":bool(mask[i]),"A_correct":bool(a[i]),"B_correct":bool(b[i]),
                        "routed_correct":bool(np.where(mask,b,a)[i]),"top10_image_ids":json.dumps([db_ids[j] for j in top[i]])})
        oracle=(~a)&b
        summary["oracle_DIAGNOSTIC_ONLY"]={**recall_at_k(route_scores(scores["cosplace"],scores[second],oracle),positives),
                                            **routing_audit(a,b,oracle),"deployable":False}
        all_metrics[str(radius)]=summary
    random={}
    primary=all_metrics[str(config["primary_radius"])]
    for budget in [10,25,50]:
        for family in ["random_budget","random_matched_net"]:
            prefix=f"{family}_budget{budget:02d}"
            values=[primary[prefix+f"_seed{s}"] for s in range(5)]
            random[prefix]={key:{"mean":float(np.mean([v[key] for v in values])),"std_population":float(np.std([v[key] for v in values],ddof=0))}
                            for key in ["R@1","R@5","R@10","invocation_fraction","rescues","harms","net_gain_percentage_points"]}
    write_json(output/"accuracy.json",{"primary_radius":config["primary_radius"],"by_radius":all_metrics,"random_all_seeds":random,
                 "sensitivity_note":"Same frozen rankings and gate masks; no refitting. Gardens +/-8 is custom positives, not GTsoft-ignore.","threshold_recalibrated":False})
    write_csv(output/"accuracy_per_query.csv",rows)
    return scores,x,masks


def benchmark(config,arrays,rows,policies,second,output,package,device,references,x,masks):
    methods=["cosplace",second];role=config["query_role"]
    indices={m:ExactCosineIndex(arrays[m]["gallery"][0]) for m in methods}
    names=["A_only","B_only"]
    names += [f"{m}_budget25" for m in ["net_benefit","trained_A_error","gap","rescue_only","net_benefit_no_std"]]
    names += [f"{family}_budget25_seed{s}" for family in ["random_budget","random_matched_net"] for s in range(5)]
    names += [f"{m}_budget{budget}" for budget in [10,50] for m in ["net_benefit","trained_A_error"]]
    measured=rows[role];summary={}
    def sync():
        if device=="cuda":torch.cuda.synchronize()
    for name in names:
        needed=["cosplace"] if name=="A_only" else [second] if name=="B_only" else methods
        encoders={m:CountEncoder(make_encoder(m,package,device)[0]) for m in needed}
        policy=ScorePolicy(policies[name])
        pipeline=None if name in {"A_only","B_only"} else ConditionalRetriever(encoders["cosplace"],indices["cosplace"],encoders[second],indices[second],policy)
        def infer(row):
            sync();started=time.perf_counter_ns()
            with Image.open(row["path"]) as image:image.load();image=image.convert("RGB")
            decoded=time.perf_counter_ns()
            if pipeline is None:
                scores,ranks=indices[needed[0]].search(encoders[needed[0]].encode([image]))
                result={"scores":scores,"ranks":ranks,"invoked_B":name=="B_only","gate_score":None}
            else:result=pipeline.infer(image)
            sync();finished=time.perf_counter_ns()
            return result,{"decode_ms":(decoded-started)/1e6,"pipeline_ms":(finished-decoded)/1e6,"total_ms":(finished-started)/1e6}
        for row in measured[:20]:infer(row)
        for encoder in encoders.values():encoder.calls=0
        if device=="cuda":torch.cuda.reset_peak_memory_stats()
        entries=[]
        for repeat in range(3):
            policy.reset()
            for i,row in enumerate(measured):
                result,elapsed=infer(row)
                assert result["invoked_B"]==bool(masks[name][1][i]),"Real causal decision differs from frozen cached reference"
                method=second if result["invoked_B"] else "cosplace"
                np.testing.assert_allclose(result["scores"],references[method][i:i+1],atol=1e-6,rtol=1e-6)
                np.testing.assert_array_equal(result["ranks"],ranking(references[method][i:i+1],10))
                entries.append({"policy":name,"pass":repeat,"query_image_id":row["image_id"],"invoked_B":result["invoked_B"],
                                "gate_score":result["gate_score"],"top1_image_id":arrays[method]["gallery"][1][result["ranks"][0,0]],**elapsed})
        a_calls=encoders["cosplace"].calls if "cosplace" in encoders else 0;b_calls=encoders[second].calls if second in encoders else 0
        assert b_calls==sum(r["invoked_B"] for r in entries) and a_calls==(0 if name=="B_only" else len(entries))
        values=np.array([r["total_ms"] for r in entries])
        summary[name]={"n_queries":len(entries),"A_forward_calls":a_calls,"B_forward_calls":b_calls,"invocation_fraction":b_calls/len(entries),
            "mean_ms":float(values.mean()),"median_ms":float(np.median(values)),"p95_ms":float(np.percentile(values,95)),
            "peak_torch_cuda_allocated_bytes":torch.cuda.max_memory_allocated() if device=="cuda" else None,
            "peak_torch_cuda_reserved_bytes":torch.cuda.max_memory_reserved() if device=="cuda" else None,
            "index_cpu_bytes":sum(indices[m].database.nbytes for m in needed),"real_rankings_and_masks_match_cached_reference":True}
        write_csv(output/(name+"_latency.csv"),entries)
        print(json.dumps({"timed":second,"policy":name,**summary[name]}),flush=True)
        pipeline=None;encoders.clear();del encoder
        if device=="cuda":torch.cuda.empty_cache()
    write_json(output/"latency.json",{"device":device,"batch_size":1,"warmup_per_policy":20,"full_passes":3,
        "real_forwards":True,"cached_query_inside_timer":False,"policies":summary,
        "includes":"warm-file decode/RGB/preprocess/causal encoders/gate/exact retrieval",
        "excludes":"checkpoint and index initialization/gallery construction/reference checks/cold filesystem",
        "memory_note":"Torch CUDA allocator peaks; not total process RSS or driver-level GPU usage. Both models resident for conditional policies.",
        "clock_note":"No system/GPU clock lock or driver modification; sequential measurements on the existing laptop."})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--package",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    package=validate_package(args.package)  # Before any final images or outputs.
    args.output.mkdir()  # Append-only: caller must supply a fresh path.
    write_json(args.output/"freeze_identity.json",{"package_sha256":digest(args.package),"package":package,
               "confirmation":json.loads((args.package.parent/"human_confirmation.json").read_text()),
               "execution_git_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()})
    device="cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(0)
    for dataset,config in package["evaluation_plan"]["datasets"].items():
        manifest=args.package.parent/package["files"][dataset+"_manifest"]["path"]
        directory=args.output/dataset;directory.mkdir()
        arrays,rows=extract(manifest,config,directory,package,device)
        for second in ["eigenplaces","dinov2"]:
            policy_path=args.package.parent/package["files"][second+"_policies"]["path"]
            metadata=json.loads(policy_path.read_text());assert metadata["B"]==second and not metadata["final_test_used"]
            policies=metadata["policies"]
            pair=directory/("pair_"+second)
            pair.mkdir()
            references,x,masks=accuracy(manifest,config,arrays,policies,second,pair)
            benchmark(config,arrays,rows,policies,second,pair,package,device,references,x,masks)
        write_json(directory/"completed.json",{"final_evaluation_complete":True,"queries":config["queries"],"no_training":True,"no_threshold_recalibration":True})
    write_json(args.output/"completed.json",{"final_evaluation_complete":True,"datasets":["nordland","gardens"],"pairs":["eigenplaces","dinov2"]})


if __name__=="__main__":main()
