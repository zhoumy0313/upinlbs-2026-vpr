"""Image manifests with explicit IDs; encoder records never expose label fields."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from PIL import Image

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def numeric_file_id(path: Path) -> int:
    groups = re.findall(r"\d+", path.stem)
    if len(groups) != 1:
        raise ValueError(f"Expected one explicit numeric image ID: {path.name}")
    return int(groups[0])


def indexed_images(folder: Path) -> list[tuple[int, Path]]:
    images = [(numeric_file_id(p), p) for p in folder.iterdir()
              if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    if not images:
        raise ValueError(f"No images in {folder}")
    ids = [i for i, _ in images]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate numeric file IDs in {folder}")
    return sorted(images, key=lambda row: row[0])


def require_aligned_ids(reference: list[tuple[int, Path]],
                        query: list[tuple[int, Path]], expected: int) -> None:
    if len(reference) != expected or len(query) != expected:
        raise ValueError(f"Expected {expected} images in each traversal")
    if [i for i, _ in reference] != [i for i, _ in query]:
        raise ValueError("Traversals have different numeric IDs; do not infer alignment from row count")


def nordland_split(frame_index: int, settings: dict) -> str:
    for key, split in [("query_train", "train"), ("query_buffer_1", "buffer"),
                       ("query_validation", "validation"), ("query_buffer_2", "buffer"),
                       ("query_test", "test")]:
        lo, hi = settings[key]
        if lo <= frame_index <= hi:
            return split
    raise ValueError(f"Frame outside declared protocol: {frame_index}")


def gardens_split(traverse: str) -> str:
    return {"day_left": "inspection_only", "day_right": "gallery",
            "night_right": "external_test"}[traverse]


def make_records(project: Path, dataset: str, traverse: str,
                 images: list[tuple[int, Path]], split_for_index) -> list[dict]:
    records = []
    for frame, (file_id, path) in enumerate(images, start=1):
        with Image.open(path) as image:
            image.load()  # Full decode: do not silently accept truncated JPEGs.
            width, height = image.size
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid image dimensions: {path}")
        records.append({"dataset": dataset, "traverse": traverse,
                        "image_id": f"{dataset}/{traverse}/{path.name}",
                        "frame_index": frame, "file_numeric_id": file_id,
                        "relative_path": str(path.resolve().relative_to(project.resolve())),
                        "sha256": file_digest(path), "split": split_for_index(frame),
                        "width": width, "height": height})
    return records


def write_manifest(path: Path, records: list[dict], protocol_sha256: str) -> None:
    ids = [r["image_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate image IDs")
    payload = {"schema_version": 1, "protocol_sha256": protocol_sha256,
               "ordering": "traverse then ascending parsed file_numeric_id; frame_index is one-based ordinal",
               "records": records}
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2)


def encoder_records(manifest_path: Path, project: Path, allowed_splits: set[str],
                    *, allow_final_test: bool = False) -> list[dict]:
    """Image-only whitelist. Caller must separately authorize final-test encoding.

    Coordinates, frame IDs, labels and correctness are deliberately not returned.
    """
    if not allowed_splits:
        raise ValueError("Explicit split selection is required")
    if {"test", "external_test"} & allowed_splits and not allow_final_test:
        raise ValueError("Final/external test encoding requires a frozen protocol authorization")
    records = json.loads(manifest_path.read_text())["records"]
    root = project.resolve()
    output, ids = [], set()
    for row in records:
        if row["split"] not in allowed_splits:
            continue
        image_id = row["image_id"]
        if image_id in ids:
            raise ValueError("Duplicate encoder image ID")
        ids.add(image_id)
        path = (root / row["relative_path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Image path must refer to an existing project file")
        output.append({"image_id": image_id, "path": str(path), "sha256": row["sha256"]})
    if not output:
        raise ValueError("No images in selected split")
    return output
