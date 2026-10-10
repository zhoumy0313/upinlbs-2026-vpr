#!/usr/bin/env python3
"""P1: verified ZIP extraction, image/ID audit and protocol manifests; no metrics."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil
import stat
import sys
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vpr_research.datasets import (file_digest, gardens_split, indexed_images, make_records,
                                   nordland_split, require_aligned_ids, write_manifest)


def extract_verified(archive, destination, expected_md5=None):
    identity = {"archive_name": archive.name, "bytes": archive.stat().st_size,
                "sha256": file_digest(archive), "md5": file_digest(archive, "md5")}
    if expected_md5 and identity["md5"] != expected_md5:
        raise ValueError("Archive does not match the protocol's official MD5")
    marker = destination / ".archive_source.json"
    if destination.exists():
        if not marker.is_file() or json.loads(marker.read_text()) != identity:
            raise ValueError("Existing raw directory has a different/unfinished source; retain it for audit")
        return identity
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination.resolve()) or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("ZIP entry escapes its directory or is a symbolic link")
        bad = zipped.testzip()
        if bad:
            raise ValueError(f"ZIP CRC failure: {bad}")
        destination.mkdir(parents=True)
        zipped.extractall(destination)
    marker.write_text(json.dumps(identity, indent=2))
    return identity


def find_traverse(raw, name):
    matches = [p for p in raw.rglob(name) if p.is_dir()]
    if len(matches) != 1:
        raise ValueError(f"Expected one traversal folder named {name}: {matches}")
    return matches[0]


def prepare(dataset, run, settings, tag):
    if dataset == "nordland":
        archive = ROOT / "data/downloads/nordland-part-2020.zip"
        raw = ROOT / "data/raw/nordland-part-2020"
        traverses, expected = ["summer", "winter"], 1750
        identity = extract_verified(archive, raw, settings["data"]["nordland"]["archive_md5"])
    else:
        archive = ROOT / "data/downloads/GardensPoint_Walking.zip"
        raw = ROOT / "data/raw/gardens-point"
        traverses, expected = ["day_left", "day_right", "night_right"], 200
        identity = extract_verified(archive, raw)
    images = {name: indexed_images(find_traverse(raw, name)) for name in traverses}
    for traverse in traverses[1:]:
        require_aligned_ids(images[traverses[0]], images[traverse], expected)
    records = []
    for traverse in traverses:
        if dataset == "nordland":
            split = (lambda _: "gallery") if traverse == "summer" else (
                lambda i: nordland_split(i, settings["data"]["nordland"]))
        else:
            split = lambda _: gardens_split(traverse)
        records.extend(make_records(ROOT, dataset, traverse, images[traverse], split))
    protocol_hash = file_digest(ROOT / "configs/protocol.yaml")
    manifest = run / f"{dataset}_manifest_{tag}.json"
    write_manifest(manifest, records, protocol_hash)
    shared = ROOT / "data/manifests" / (run.name + "_" + manifest.name)
    if shared.exists():
        raise ValueError("Shared manifest already exists; use a new run/tag")
    shutil.copy2(manifest, shared)
    duplicates = defaultdict(list)
    for row in records:
        duplicates[(row["traverse"], row["sha256"])].append(row["image_id"])
    report = {"dataset": dataset, "archive": identity, "images_decoded": len(records),
              "counts_by_traverse": dict(Counter(r["traverse"] for r in records)),
              "counts_by_split": dict(Counter(r["split"] for r in records)),
              "numeric_ids_aligned_across_traverses": True,
              "raw_file_numeric_id_range": [images[traverses[0]][0][0], images[traverses[0]][-1][0]],
              "within_traverse_duplicate_image_groups": [ids for ids in duplicates.values() if len(ids) > 1],
              "manifest": str(shared.relative_to(ROOT)), "manifest_sha256": file_digest(shared),
              "protocol_sha256": protocol_hash, "label_metrics_computed": False,
              "note": "Matching file IDs plus source correspondence support alignment; inspect representative image pairs. No cross-traverse retrieval or final-test evaluation performed."}
    with (run / f"{dataset}_data_audit_{tag}.json").open("x") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["nordland", "gardens_point"], required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest-tag", choices=["v2"], default="v2",
                        help="v2 marks unused Gardens Point day_left as inspection_only")
    args = parser.parse_args()
    run = args.run_dir.resolve()
    if run.parent != ROOT / "outputs":
        raise ValueError("Use a project output run directory")
    run.mkdir(exist_ok=True)
    settings = yaml.safe_load((ROOT / "configs/protocol.yaml").read_text())
    prepare(args.dataset, run, settings, args.manifest_tag)


if __name__ == "__main__":
    main()
