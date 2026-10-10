#!/usr/bin/env python3
"""Package exact development decisions without opening final-test results."""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from frozen_package import digest,validate_package


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument("--development-run",type=Path,required=True)
    args=parser.parse_args()
    out=args.run_dir;out.mkdir(parents=True,exist_ok=True)
    dev=args.development_run
    assert json.loads((dev/"phase_acceptance.json").read_text())["passed"]
    if subprocess.check_output(["git","status","--porcelain"],text=True).strip():
        raise ValueError("Commit the reviewable code/config before constructing a freeze package")
    original=ROOT/"outputs/p3_dinov2_stable_20261010_141000"
    fallback=json.loads((dev/"fallback_decision.json").read_text())
    assert fallback["replacement_count"]==1 and not fallback["final_test_seen"]
    originals={
        "nordland_manifest":ROOT/"data/manifests/p1_20261010_132030_nordland_manifest_v2.json",
        "gardens_manifest":ROOT/"data/manifests/p1_20261010_132030_gardens_point_manifest_v2.json",
        "eigenplaces_policies":dev/"gate_development/policies.json",
        "dinov2_policies":original/"gate_development/policies.json",
        "fallback_decision":dev/"fallback_decision.json",
        "eigenplaces_development_metrics":dev/"gate_development/metrics.json",
        "dinov2_development_metrics":original/"gate_development/metrics.json"}
    files={}
    for name,source in originals.items():
        target=out/(name+".json")
        with target.open("xb") as stream:stream.write(source.read_bytes())
        files[name]={"path":target.name,"sha256":digest(target),"original":str(source.resolve())}
    config=yaml.safe_load((ROOT/"configs/protocol.yaml").read_text())
    config["status"]="prospective_freeze_review_not_preregistered"
    config["models"]["original_B"]=config["models"]["B"]
    config["models"]["B"]=config["models"]["fallback_B"]
    config["models"]["replacement_count"]=1
    with (out/"effective_protocol.yaml").open("x") as stream:yaml.safe_dump(config,stream,sort_keys=False)
    files["effective_protocol"]={"path":"effective_protocol.yaml","sha256":digest(out/"effective_protocol.yaml")}
    model_sources=json.loads((ROOT/"configs/model_sources.json").read_text())
    fp_paths={"cosplace":dev/"cosplace/fingerprint.json","eigenplaces":dev/"eigenplaces/fingerprint.json",
              "dinov2":ROOT/"outputs/p2_20261010_134300/dinov2/fingerprint.json"}
    states={}
    for method,path in fp_paths.items():
        states[method]=json.loads(path.read_text())["model"]["model_state_sha256"]
        source=model_sources[method]
        assert digest(ROOT/source["checkpoint"])==source["checkpoint_sha256"]
    paths=[]
    for directory,suffixes in [("src",{".py"}),("scripts",{".py",".sh"}),("tests",{".py"}),("configs",{".yaml",".json"})]:
        paths += [p for p in (ROOT/directory).rglob("*") if p.is_file() and p.suffix in suffixes and "__pycache__" not in p.parts and p.name!="authors.json"]
    package={"status":"ready_for_human_confirmation","created_at":dt.datetime.now(dt.timezone.utc).isoformat(),
             "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
             "final_test_seen_before_freeze":False,"human_confirmation_required":True,
             "development_run":str(dev.resolve()),"code_config_sha256":{str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)},
             "files":files,"models":{m:model_sources[m] for m in states},"model_state_sha256":states,
             "evaluation_plan":{"model_pairs":[["cosplace","eigenplaces"],["cosplace","dinov2"]],
                "accuracy_policies":"All 50 previously fitted policies per pair; report all seeds and ablations",
                "datasets":{"nordland":{"gallery":1750,"query_role":"test","queries":650,"primary_radius":5,"sensitivity_radii":[1,10]},
                            "gardens":{"gallery":200,"query_role":"external_test","queries":200,"primary_radius":0,"sensitivity_radii":[8]}},
                "timed_policies":"A-only, B-only and all 15 conditional policies at budget25 (including all five seeds for both random controls); additionally net-benefit and two-head A-error at budget10 and budget50",
                "timing":{"batch_size":1,"warmup_queries":20,"full_query_passes":3,"synchronize_cuda":True},
                "no_final_training_or_threshold_recalibration":True,"random_matched_cost_note":"Matched to validation invocation count only; final actual rates can differ and must be reported, without test recalibration.",
                "oracle":"Top1 correctness oracle for diagnostics only; never time or deploy it",
                "SU":"Excluded numerical comparator: no verified official code/complete numerical convention; cite as related work and disclose missing comparison",
                "paper_claim":"Empirical budget allocation study and failure analysis; no claim that net-benefit outperforms the error predictor without final evidence"}}
    with (out/"selection.json").open("x") as stream:json.dump(package,stream,indent=2,allow_nan=False)
    validate_package(out/"selection.json",require_confirmation=False)
    print(json.dumps({"package":str((out/"selection.json").resolve()),"sha256":digest(out/"selection.json"),"status":package["status"]},indent=2))


if __name__=="__main__":main()
