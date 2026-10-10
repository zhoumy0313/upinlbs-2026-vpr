#!/usr/bin/env python3
"""Actual checkpoint/CLS/batch/ordering smoke check using summer images only."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vpr_research.core import cosine_scores, ranking
from vpr_research.datasets import encoder_records
from vpr_research.encoders.frozen import create_encoder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--methods", nargs="+", choices=["cosplace", "dinov2", "eigenplaces"], default=["cosplace", "dinov2"])
    args = parser.parse_args()
    torch.manual_seed(0)
    rows = encoder_records(args.manifest, ROOT, {"gallery"})[:16]
    images = []
    for row in rows:
        with Image.open(row["path"]) as image:
            images.append(image.convert("RGB"))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    result = {"synthetic_labels": False, "scope": "same summer images; no winter/final labels", "models": {}}
    for method in args.methods:
        encoder = create_encoder(method, device)
        batch = encoder.encode(images)
        single = np.concatenate([encoder.encode([im]) for im in images])
        np.testing.assert_allclose(batch, single, atol=2e-5, rtol=2e-5)
        np.testing.assert_allclose(np.linalg.norm(batch, axis=1), 1, atol=1e-5)
        np.testing.assert_array_equal(ranking(cosine_scores(single, single), 1)[:, 0], np.arange(len(rows)))
        assert not encoder.model.training and all(not p.requires_grad for p in encoder.model.parameters())
        tensor = encoder.prepare(images[:1])
        descriptor = encoder.encode_tensor(tensor)
        assert not descriptor.requires_grad
        if method in {"dinov2", "eigenplaces"}:
            with torch.inference_mode():
                reference = encoder.model(tensor.to(encoder.device))
                reference /= reference.norm(dim=1, keepdim=True)
            torch.testing.assert_close(descriptor, reference)
        fingerprint = encoder.fingerprint()
        (args.run_dir / f"{method}_probe_fingerprint.json").write_text(json.dumps(fingerprint, indent=2))
        result["models"][method] = {"device": device, "shape": list(batch.shape),
                                    "batch_vs_single_max_abs_diff": float(abs(batch-single).max()),
                                    "all_same_image_self_matches": True, "inference_and_eval_frozen": True,
                                    "cls_equals_official_forward": True if method == "dinov2" else None,
                                    "equals_official_forward": True if method in {"dinov2", "eigenplaces"} else None}
        del encoder
        if device == "cuda":
            torch.cuda.empty_cache()
    with (args.run_dir / "encoder_probe.json").open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
