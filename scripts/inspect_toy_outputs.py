#!/usr/bin/env python3
"""Explain and verify saved OFFICIAL toy inference, without ground truth."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import faiss
import numpy as np
from PIL import Image


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    repo = root / "third_party/VPR-methods-evaluation"
    run = args.run_dir.resolve()
    assert run.parent == root / "outputs", "Use a project output run directory"
    sys.path.insert(0, str(repo))
    from test_dataset import TestDataset
    # Only the shipped unlabelled toy: never accept research data/GT paths.
    ds = TestDataset(str(repo / "toy_dataset/database"), str(repo / "toy_dataset/queries"),
                     image_size=[200, 200], use_labels=False)
    toy_logs = sorted(p for parent in run.glob("official_toy*") if parent.is_dir()
                      for p in parent.iterdir() if (p / "queries_descriptors.npy").is_file())
    assert len(toy_logs) == 1, "Expected one successful official toy run; retain failed logs separately"
    toy = toy_logs[0]
    db = np.load(toy / "database_descriptors.npy")
    q = np.load(toy / "queries_descriptors.npy")
    assert db.shape == (ds.num_database, 512) and q.shape == (ds.num_queries, 512)
    assert np.isfinite(db).all() and np.isfinite(q).all()
    db_norm = np.linalg.norm(db, axis=1)
    q_norm = np.linalg.norm(q, axis=1)
    assert np.allclose(db_norm, 1, atol=1e-5) and np.allclose(q_norm, 1, atol=1e-5)
    normalized_db = db / db_norm[:, None]
    normalized_q = q / q_norm[:, None]
    scores = normalized_q @ normalized_db.T
    cosine_rank = np.argsort(-scores, axis=1, kind="stable")
    index = faiss.IndexFlatL2(512)
    index.add(db)
    distances, l2_rank = index.search(q, len(db))
    np.testing.assert_array_equal(cosine_rank, l2_rank)
    np.testing.assert_allclose(distances, np.take_along_axis(2 - 2 * scores, l2_rank, axis=1), atol=2e-6)

    manifest = []
    for role, paths in [("database", ds.database_paths), ("queries", ds.queries_paths)]:
        for row, path in enumerate(paths):
            path = Path(path)
            with Image.open(path) as img:
                img.load()
                width, height = img.size
            manifest.append({"role": role, "descriptor_row": row, "image_id": path.name,
                             "relative_path": str(path.relative_to(repo)), "sha256": digest(path),
                             "width": width, "height": height})
    with (run / "toy_manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
    with (run / "matches.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["query_id", "query_row", "rank", "database_id",
                                                   "database_row", "cosine_similarity", "squared_l2_distance"])
        writer.writeheader()
        for qi, indices in enumerate(l2_rank):
            for ri, di in enumerate(indices):
                writer.writerow({"query_id": Path(ds.queries_paths[qi]).name, "query_row": qi,
                                 "rank": ri + 1, "database_id": Path(ds.database_paths[di]).name,
                                 "database_row": int(di), "cosine_similarity": float(scores[qi, di]),
                                 "squared_l2_distance": float(distances[qi, ri])})
            lines = (toy / "preds" / f"{qi:03d}.txt").read_text().splitlines()
            actual = [Path(s).name for s in lines[lines.index("Predictions paths:") + 1:] if s.strip()]
            assert actual == [Path(ds.database_paths[di]).name for di in indices[:3]]
    image_tensor, _ = ds[0]
    assert tuple(image_tensor.shape) == (3, 200, 200)
    checks = {"stage": "E0_unlabelled_official_toy_only", "database_shape": list(db.shape),
              "queries_shape": list(q.shape), "similarity_matrix_shape": list(scores.shape),
              "image_tensor_shape": list(image_tensor.shape), "descriptor_dtype": str(db.dtype),
              "database_norm_range": [float(db_norm.min()), float(db_norm.max())],
              "query_norm_range": [float(q_norm.min()), float(q_norm.max())],
              "all_images_decoded": len(manifest), "cosine_l2_full_rank_agreement": True,
              "saved_official_top3_agreement": True, "recall": None,
              "note": "No ground truth was loaded. Rankings are candidates, not accuracy or pose results.",
              "top3": [{"query_id": Path(ds.queries_paths[qi]).name,
                        "candidates": [{"image_id": Path(ds.database_paths[di]).name,
                                        "cosine": float(scores[qi, di])} for di in inds[:3]]}
                       for qi, inds in enumerate(l2_rank)]}
    with (run / "toy_checks.json").open("x") as stream:
        json.dump(checks, stream, indent=2)
    cache_root = root / "weights/p0_torch/hub"
    model_files = {str(p.relative_to(cache_root)): digest(p)
                   for p in sorted(cache_root.rglob("*.py"))}
    model_files.update({str(p.relative_to(cache_root)): digest(p)
                        for p in sorted((cache_root / "checkpoints").glob("*")) if p.is_file()})
    fingerprint = {
        "dataset": "official repository toy_dataset (unlabelled)",
        "manifest_sha256": digest(run / "toy_manifest.json"),
        "protocol_sha256": digest(root / "configs/protocol.yaml"),
        "method": "CosPlace", "backbone": "ResNet18", "dimension": 512,
        "dtype": "float32", "pooling": "CosPlace L2 -> GeM -> Flatten -> Linear -> L2 (verify hub code)",
        "preprocessing": {"color": "RGB", "size_hw": [200, 200],
                          "order": "ToTensor -> ImageNet Normalize -> tensor Resize",
                          "interpolation": "torchvision Resize default bilinear", "antialias": True,
                          "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
        "scope_note": "Official 200x200 smoke test; research protocol 224x224 was not changed.",
        "evaluator_commit": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
        "hub_source_and_checkpoint_sha256": model_files,
        "descriptor_files_sha256": {p.name: digest(p) for p in toy.glob("*_descriptors.npy")},
        "dataset_source_sha256": digest(repo / "test_dataset.py"),
        "inspector_source_sha256": digest(Path(__file__)),
    }
    with (run / "toy_fingerprint.json").open("x") as stream:
        json.dump(fingerprint, stream, indent=2)
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
