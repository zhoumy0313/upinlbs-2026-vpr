#!/usr/bin/env python3
"""Encode fixed Nordland summer gallery and winter train/validation only."""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vpr_research.artifacts import extraction_code_identity
from vpr_research.datasets import encoder_records, file_digest
from vpr_research.encoders.frozen import create_encoder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--method", choices=["cosplace", "dinov2", "eigenplaces"], required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    settings = yaml.safe_load((ROOT / "configs/protocol.yaml").read_text())
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(0)
    encoder = create_encoder(args.method, device, settings["preprocessing"]["initial_research_setting"]["resize_hw"])
    out = args.run_dir / args.method
    out.mkdir()  # Never overwrite descriptors from an old or failed experiment.
    arrays, stats = {}, {}
    for role, expected_count in [("gallery",1750), ("train",600), ("validation",300)]:
        rows = encoder_records(args.manifest, ROOT, {role})
        traverse = "summer" if role == "gallery" else "winter"
        if len(rows) != expected_count or not all(r["image_id"].startswith(f"nordland/{traverse}/") for r in rows):
            raise ValueError("Expected the exact protocol development split")
        output = []
        started = time.perf_counter()
        for i, row in enumerate(rows):
            if file_digest(Path(row["path"])) != row["sha256"]:
                raise ValueError("Image content differs from its manifest")
            with Image.open(row["path"]) as image:
                output.append(encoder.encode([image]))
            if (i + 1) % 250 == 0 or i + 1 == len(rows):
                print(json.dumps({"method":args.method,"role":role,"encoded":i+1,"total":len(rows)}), flush=True)
        if device == "cuda":
            torch.cuda.synchronize()
        values = np.concatenate(output)
        if values.dtype != np.float32 or values.shape != (expected_count, encoder.dimension):
            raise ValueError("Unexpected descriptor dtype/shape")
        np.testing.assert_allclose(np.linalg.norm(values,axis=1),1,atol=1e-5)
        target = out / f"{role}_descriptors.npy"
        np.save(target, values)
        (out / f"{role}_image_ids.json").write_text(json.dumps([r["image_id"] for r in rows], indent=2))
        arrays[role] = file_digest(target)
        stats[role] = {"images": len(rows), "descriptor_shape":list(values.shape),
                       "array_bytes":values.nbytes, "npy_file_bytes":target.stat().st_size,
                       "offline_build_wall_seconds":time.perf_counter()-started,
                       "includes": "file hash, decode, preprocess, batch1 inference, CPU output and saving",
                       "not_online_latency":True}
    fingerprint = {"manifest":str(args.manifest.resolve()),"manifest_sha256":file_digest(args.manifest),
                   "extraction_code":extraction_code_identity(),"model":encoder.fingerprint(),
                   "arrays_sha256":arrays,"batch_size":1,"device":device,
                   "numpy":np.__version__,"roles":["gallery","train","validation"],
                   "final_query_encoding_performed":False}
    (out / "fingerprint.json").write_text(json.dumps(fingerprint,indent=2))
    (out / "build_stats.json").write_text(json.dumps(stats,indent=2))
    print(json.dumps(stats,indent=2))


if __name__ == "__main__":
    main()
