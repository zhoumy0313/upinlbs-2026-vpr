#!/usr/bin/env python3
"""Record the single protocol-permitted replacement before seeing its results."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-run",type=Path,required=True)
    args=parser.parse_args()
    metrics=args.original_run/"gate_development/metrics.json"
    result=json.loads(metrics.read_text())
    assert result["development_only"] and not result["final_test_used"]
    val=result["splits"]["validation"]
    assert val["B_only"]["R@1"]<val["A_only"]["R@1"]
    assert all(val[f"net_benefit_budget{b}"]["invocation_fraction"]==0 for b in [10,25,50])
    decision={"recorded_at":dt.datetime.now(dt.timezone.utc).isoformat(),
              "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
              "evidence_run":str(args.original_run.resolve()),
              "evidence_metrics_sha256":hashlib.sha256(metrics.read_bytes()).hexdigest(),
              "original_B":"DINOv2 ViT-S14 CLS/384", "replacement_B":"EigenPlaces ResNet50/512",
              "replacement_count":1,"further_replacements_allowed":False,"final_test_seen":False,
              "reason":"Original B is weaker than A on validation; fixed benefit gate invokes B zero times at all budgets. Evaluate the sole predeclared alternative without promising improvement.",
              "original_validation":{"A_R1":val["A_only"]["R@1"],"B_R1":val["B_only"]["R@1"],
                                     "net_gate_invocations_at_all_budgets":0},
              "constraints":"Retain original pair and failures. Only train/validation; no encoder fine-tuning, feature additions, hyperparameter search or final-test model selection."}
    output=args.original_run/"fallback_decision.json"
    with output.open("x") as stream:json.dump(decision,stream,indent=2)
    snapshot=args.original_run/"original_source_before_fallback";snapshot.mkdir()
    for directory in ["src","scripts","configs","tests"]:
        for path in (ROOT/directory).rglob("*"):
            if path.is_file() and path.suffix in {".py",".sh",".yaml",".json"} and "__pycache__" not in path.parts:
                dest=snapshot/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    print(output)


if __name__=="__main__":main()
