"""Descriptor artifact identity/validation independent of correctness labels."""
import json
from pathlib import Path
import subprocess

import numpy as np

from .datasets import encoder_records, file_digest

ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_SOURCES = ["src/vpr_research/encoders/frozen.py", "src/vpr_research/datasets.py",
                      "src/vpr_research/artifacts.py", "scripts/extract_dev_descriptors.py",
                      "configs/model_sources.json", "configs/protocol.yaml"]


def extraction_code_identity():
    return {"git_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
            "files_sha256": {name: file_digest(ROOT / name) for name in EXTRACTION_SOURCES}}


def load_descriptors(directory: Path, manifest: Path, role: str):
    """Reject mismatched IDs, source/config/content/dtype; no silent cache reuse."""
    if role not in {"gallery", "train", "validation"}:
        raise ValueError("This development loader excludes final-test query artifacts")
    fingerprint = json.loads((directory / "fingerprint.json").read_text())
    if fingerprint["manifest_sha256"] != file_digest(manifest):
        raise ValueError("Descriptor manifest identity mismatch")
    expected_code = extraction_code_identity()["files_sha256"]
    if fingerprint["extraction_code"]["files_sha256"] != expected_code:
        raise ValueError("Descriptor extraction code/config changed; rebuild or explicitly version adaptation")
    ids = json.loads((directory / f"{role}_image_ids.json").read_text())
    expected = [r["image_id"] for r in encoder_records(manifest, ROOT, {role})]
    if ids != expected:
        raise ValueError("Descriptor row IDs do not match the declared split order")
    array_path = directory / f"{role}_descriptors.npy"
    if file_digest(array_path) != fingerprint["arrays_sha256"][role]:
        raise ValueError("Descriptor file changed after fingerprint creation")
    features = np.load(array_path, allow_pickle=False)
    dimension = fingerprint["model"]["dimension"]
    if features.dtype != np.float32 or features.shape != (len(ids), dimension) or not np.isfinite(features).all():
        raise ValueError("Invalid descriptor shape/dtype/value")
    if not np.allclose(np.linalg.norm(features, axis=1), 1, atol=1e-5):
        raise ValueError("Descriptors must have unit L2 norms")
    return features, ids, fingerprint
