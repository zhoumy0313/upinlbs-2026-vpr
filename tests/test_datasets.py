import json
from pathlib import Path

from PIL import Image
import pytest

from vpr_research.datasets import (encoder_records, gardens_split, indexed_images, make_records,
                                   nordland_split, require_aligned_ids, write_manifest)


SETTINGS = {"query_train": [1, 600], "query_buffer_1": [601, 700],
            "query_validation": [701, 1000], "query_buffer_2": [1001, 1100],
            "query_test": [1101, 1750]}


def test_numeric_order_and_duplicate_id(tmp_path):
    for name in ["Image10.jpg", "Image2.jpg", "Image1.jpg"]:
        Image.new("RGB", (4, 4)).save(tmp_path / name)
    assert [i for i, _ in indexed_images(tmp_path)] == [1, 2, 10]
    Image.new("RGB", (4, 4)).save(tmp_path / "Image01.png")
    with pytest.raises(ValueError, match="Duplicate"):
        indexed_images(tmp_path)


def test_alignment_checks_ids_not_just_count():
    ref = [(1, Path("a")), (2, Path("b"))]
    query = [(1, Path("c")), (3, Path("d"))]
    with pytest.raises(ValueError, match="different numeric IDs"):
        require_aligned_ids(ref, query, 2)


def test_split_boundaries_and_counts():
    expected = {1: "train", 600: "train", 601: "buffer", 700: "buffer",
                701: "validation", 1000: "validation", 1001: "buffer", 1100: "buffer",
                1101: "test", 1750: "test"}
    for i, split in expected.items():
        assert nordland_split(i, SETTINGS) == split
    from collections import Counter
    assert Counter(nordland_split(i, SETTINGS) for i in range(1, 1751)) == {
        "train": 600, "buffer": 200, "validation": 300, "test": 650}
    with pytest.raises(ValueError):
        nordland_split(0, SETTINGS)


def test_gardens_gallery_excludes_auxiliary_day_left():
    assert gardens_split("day_left") == "inspection_only"
    assert gardens_split("day_right") == "gallery"
    assert gardens_split("night_right") == "external_test"


def test_full_decode_rejects_corrupt_image(tmp_path):
    path = tmp_path / "Image1.jpg"
    path.write_bytes(b"not an image")
    with pytest.raises(OSError):
        make_records(tmp_path, "fixture", "summer", [(1, path)], lambda _: "gallery")


def test_encoder_whitelist_and_final_test_restriction(tmp_path):
    path = tmp_path / "Image1.jpg"
    Image.new("RGB", (4, 4)).save(path)
    rows = make_records(tmp_path, "fixture", "winter", [(1, path)], lambda _: "train")
    rows[0].update(positives=["hidden"], correctness=True, B_score=.9, coordinate=42)
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, rows, "fixturehash")
    got = encoder_records(manifest, tmp_path, {"train"})
    assert set(got[0]) == {"image_id", "path", "sha256"}
    for split in ["test", "external_test"]:
        with pytest.raises(ValueError, match="frozen protocol"):
            encoder_records(manifest, tmp_path, {split})
    with pytest.raises(ValueError, match="Explicit"):
        encoder_records(manifest, tmp_path, set())


def test_manifest_duplicate_ids_rejected(tmp_path):
    row = {"image_id": "duplicate"}
    with pytest.raises(ValueError, match="Duplicate"):
        write_manifest(tmp_path / "manifest.json", [row, row], "fixturehash")


def test_manifest_path_cannot_escape_project(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": [{"split": "train", "image_id": "x",
                                               "relative_path": "../outside.jpg", "sha256": "x"}]}))
    with pytest.raises(ValueError, match="existing project file"):
        encoder_records(manifest, tmp_path, {"train"})
