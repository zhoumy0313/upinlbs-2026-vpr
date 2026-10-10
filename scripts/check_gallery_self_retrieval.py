#!/usr/bin/env python3
"""P1 integration check: only same-image gallery self-retrieval, no query labels."""
import argparse
import csv
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
from vpr_research.datasets import encoder_records, file_digest
from vpr_research.encoders.frozen import CosPlaceEncoder
from vpr_research.core import cosine_scores, ranking


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", choices=["gardens_point", "nordland"], required=True)
    parser.add_argument("--limit", type=int, default=0,
                        help="0 checks the entire gallery; otherwise select evenly spaced gallery images")
    args = parser.parse_args()
    # No access to night/winter query images or a ground-truth file through this adapter.
    rows = encoder_records(args.manifest, ROOT, {"gallery"})
    expected_traverse = "day_right" if args.dataset == "gardens_point" else "summer"
    if not all(row["image_id"].split("/")[1] == expected_traverse for row in rows):
        raise ValueError("Gallery must match the protocol traversal; exclude auxiliary images")
    if args.limit:
        if not 1 <= args.limit <= len(rows):
            raise ValueError("Invalid self-check sample count")
        rows = [rows[i] for i in np.linspace(0, len(rows) - 1, args.limit, dtype=int)]
    settings = yaml.safe_load((ROOT / "configs/protocol.yaml").read_text())
    device = "cuda" if torch.cuda.is_available() else "cpu"
    encoder = CosPlaceEncoder(device, settings["preprocessing"]["initial_research_setting"]["resize_hw"])
    outputs = []
    started = time.monotonic()
    for row in rows:
        if file_digest(Path(row["path"])) != row["sha256"]:
            raise ValueError("Image content changed after manifest creation")
        with Image.open(row["path"]) as image:
            outputs.append(encoder.encode([image]))
    features = np.concatenate(outputs)
    scores = cosine_scores(features, features)
    best = ranking(scores, 1)[:, 0]
    offdiagonal = scores.copy()
    np.fill_diagonal(offdiagonal, -np.inf)
    ambiguous = np.flatnonzero(np.max(offdiagonal, axis=1) >= np.diag(scores) - 1e-10)
    out = args.run_dir / (args.dataset + "_self_retrieval")
    out.mkdir()
    np.save(out / "gallery_descriptors.npy", features)
    (out / "image_ids.json").write_text(json.dumps([r["image_id"] for r in rows], indent=2))
    fingerprint = {"manifest_sha256": file_digest(args.manifest), "manifest": str(args.manifest.resolve()),
                   "image_ids": [r["image_id"] for r in rows], "model": encoder.fingerprint(),
                   "protocol_sha256": file_digest(ROOT / "configs/protocol.yaml"),
                   "scope": "same image gallery self-retrieval; no cross-traverse or final-test evaluation"}
    (out / "fingerprint.json").write_text(json.dumps(fingerprint, indent=2))
    with (out / "per_image.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["image_id", "top1_image_id", "self_top1", "self_cosine"])
        for i, row in enumerate(rows):
            writer.writerow([row["image_id"], rows[best[i]]["image_id"], bool(best[i] == i), float(scores[i, i])])
    result = {"dataset": args.dataset, "n_gallery_checked": len(rows), "descriptor_shape": list(features.shape),
              "top1_self_matches": int((best == np.arange(len(rows))).sum()),
              "exact_self_top1_fraction": float((best == np.arange(len(rows))).mean()),
              "ambiguous_self_ids": [rows[i]["image_id"] for i in ambiguous],
              "wall_seconds": time.monotonic() - started, "device": device,
              "cross_traverse_recall_computed": False,
              "note": "Same image encoder/pipeline integration check; not VPR performance or online latency."}
    (out / "metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if result["top1_self_matches"] != len(rows):
        raise ValueError("Self-retrieval mismatch/duplicate descriptors; inspect saved IDs rather than remove images")


if __name__ == "__main__":
    main()
