#!/usr/bin/env python3
"""Compare two real development runs and retain synthetic cache corruption probes."""
import argparse
import json
from pathlib import Path
import shutil
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from vpr_research.artifacts import load_descriptors


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument("--repeat-dir",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    args=parser.parse_args()
    result={"stage":"P2","development_only":True,"final_test_metrics_computed":False,"models":{}}
    for method in ["cosplace","dinov2"]:
        differences={}
        for role,count in [("gallery",1750),("train",600),("validation",300)]:
            original,ids,fp=load_descriptors(args.run_dir/method,args.manifest,role)
            repeat,rids,rfp=load_descriptors(args.repeat_dir/method,args.manifest,role)
            assert len(ids)==count and ids==rids
            np.testing.assert_allclose(original,repeat,atol=1e-6,rtol=1e-6)
            assert fp["model"]["model_state_sha256"]==rfp["model"]["model_state_sha256"]
            assert fp["final_query_encoding_performed"] is False and rfp["final_query_encoding_performed"] is False
            assert set(fp["roles"])=={"gallery","train","validation"}
            assert fp["model"]["all_parameters_frozen"] and fp["model"]["eval_mode"]
            assert not fp["model"]["numerics"]["cudnn_tf32"]
            differences[role]=float(abs(original-repeat).max())
        result["models"][method]={"rows_and_descriptor_repeat_verified":True,"max_abs_difference":differences}
    original=json.loads((args.run_dir/"dev_baselines/metrics.json").read_text())
    repeat=json.loads((args.repeat_dir/"dev_baselines/metrics.json").read_text())
    for role in ["train","validation"]:
        for key in ["A_CosPlace","B_DINOv2","complementarity_counts","oracle_R1_DIAGNOSTIC_ONLY"]:
            assert original["splits"][role][key]==repeat["splits"][role][key]
        for method in ["cosplace","dinov2"]:
            a=np.load(args.run_dir/"dev_baselines"/f"{role}_{method}_scores.npy")
            b=np.load(args.repeat_dir/"dev_baselines"/f"{role}_{method}_scores.npy")
            np.testing.assert_allclose(a,b,atol=1e-6,rtol=1e-6)
    measurements=json.loads((args.repeat_dir/"dev_latency.json").read_text())
    assert measurements["cached_query_descriptors_used_for_timing"] is False
    assert measurements["passes"]==3 and measurements["batch_size"]==1
    assert all(m["n_measured"]==192 and m["real_forward_outputs_match_cached_reference"] for m in measurements["models"].values())
    commands=[json.loads(line) for line in (args.repeat_dir/"commands.jsonl").read_text().splitlines()]
    assert len(commands)==9 and all(c["exit_status"]==0 for c in commands)
    assert "22 passed" in (args.repeat_dir/"unit_tests.log").read_text()
    faults=args.run_dir/"synthetic_cache_corruption_probes"
    faults.mkdir()
    errors={}
    for name in ["wrong_ids","changed_descriptor","changed_extraction_identity"]:
        folder=faults/name;folder.mkdir()
        for file in ["fingerprint.json","validation_image_ids.json","validation_descriptors.npy"]:
            shutil.copy2(args.run_dir/"cosplace"/file,folder/file)
        if name=="wrong_ids":
            ids=json.loads((folder/"validation_image_ids.json").read_text());ids[0],ids[1]=ids[1],ids[0]
            (folder/"validation_image_ids.json").write_text(json.dumps(ids))
        elif name=="changed_descriptor":
            values=np.load(folder/"validation_descriptors.npy");values[0,0]+=.1
            np.save(folder/"validation_descriptors.npy",values)
        else:
            fp=json.loads((folder/"fingerprint.json").read_text());fp["extraction_code"]["files_sha256"]["configs/protocol.yaml"]="synthetic_invalid_hash"
            (folder/"fingerprint.json").write_text(json.dumps(fp))
        try:
            load_descriptors(folder,args.manifest,"validation")
        except ValueError as error:
            expected={"wrong_ids":"row IDs","changed_descriptor":"changed after","changed_extraction_identity":"code/config changed"}[name]
            assert expected in str(error)
            errors[name]=str(error)
        else:raise AssertionError("Corrupted cache was accepted")
    try:load_descriptors(args.run_dir/"cosplace",args.manifest,"test")
    except ValueError as error:errors["final_test_loader_guard"]=str(error)
    else:raise AssertionError("Development loader accepted a final-test artifact")
    result.update({"status":"passed","unit_tests":22,"complete_reproduction_commands":9,
                   "baseline_and_complementarity_repeat_identical":True,"cache_faults_rejected":errors,
                   "latency_each_model_real_forward_samples":192,"repeat_dir":str(args.repeat_dir.resolve())})
    with (args.run_dir/"phase_acceptance.json").open("x") as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
