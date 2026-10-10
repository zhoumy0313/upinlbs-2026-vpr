"""Synthetic aligned-ID final evaluator fixture, never real held-out images."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("final_evaluator",ROOT/"scripts/run_frozen_evaluation.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_id_alignment_rescue_harm_and_sensitivity_keep_frozen_decisions(tmp_path):
    manifest=tmp_path/"synthetic_manifest.json"
    db=[f"synthetic/d{i}" for i in range(1,13)];query=["synthetic/q1","synthetic/q2"]
    manifest.write_text(json.dumps({"records":[{"image_id":i,"frame_index":j} for j,i in enumerate(db,1)]+
        [{"image_id":query[0],"frame_index":2},{"image_id":query[1],"frame_index":10}]}))
    basis=np.eye(12,dtype=np.float32)
    arrays={"cosplace":{"gallery":(basis,db),"external_test":(basis[[6,9]],query)},
            "eigenplaces":{"gallery":(basis,db),"external_test":(basis[[1,4]],query)}}
    threshold={"kind":"finite","value":0.5}
    policies={"A_only":{"kind":"always_A","threshold":threshold,"heads":[]},
              "B_only":{"kind":"always_B","threshold":threshold,"heads":[]},
              "gap":{"kind":"gap","threshold":{"kind":"finite","value":-1.5},"heads":[]}}
    for budget in [10,25,50]:
        for family in ["random_budget","random_matched_net"]:
            for seed in range(5):policies[f"{family}_budget{budget}_seed{seed}"]={"kind":"random","seed":seed,"threshold":threshold,"heads":[]}
    config={"query_role":"external_test","primary_radius":0,"sensitivity_radii":[8]}
    scores,features,masks=module.accuracy(manifest,config,arrays,policies,"eigenplaces",tmp_path)
    result=json.loads((tmp_path/"accuracy.json").read_text())
    strict=result["by_radius"]["0"];relaxed=result["by_radius"]["8"]
    assert strict["A_only"]["R@1"]==strict["B_only"]["R@1"]==0.5
    assert strict["gap"]["rescues"]==strict["gap"]["harms"]==1
    assert strict["gap"]["net_gain_percentage_points"]==0
    assert relaxed["A_only"]["R@1"]==relaxed["B_only"]["R@1"]==1
    assert all(strict[n]["n_invoked"]==relaxed[n]["n_invoked"] for n in policies)
    assert not result["threshold_recalibrated"]
    assert features.shape==(2,5) and masks["gap"][1].all()
