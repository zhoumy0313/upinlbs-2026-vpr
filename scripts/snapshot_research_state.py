#!/usr/bin/env python3
"""Record non-secret code/config provenance without inspecting credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [ROOT / name for name in ["AGENTS.md", "PLAN.md", "requirements-core.txt", "pytest.ini", ".gitignore"]]
    for directory, suffixes in [("src", {".py"}), ("scripts", {".py", ".sh"}),
                                ("tests", {".py"}), ("configs", {".yaml", ".json"})]:
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and p.suffix in suffixes)
    files = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    sources = {}
    for repository, filenames in {
        "VPR_Tutorial": ["README.md", "datasets/load_dataset.py", "evaluation/metrics.py"],
        "DeltaDescriptors": ["README.md", "src/outFuncs.py"],
    }.items():
        directory = ROOT / "third_party" / repository
        commit = subprocess.check_output(["git", "-C", str(directory), "rev-parse", "HEAD"], text=True).strip()
        sources[repository] = {"git_commit": commit,
                               "files_sha256": {name: digest(directory / name) for name in filenames}}
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    result = {"files_sha256": files, "author_sources": sources,
              "git_commit": commit.stdout.strip() if commit.returncode == 0 else None,
              "note": "Source/config identity snapshot; frozen-model/manifest identities are in each run's fingerprint. No environment secrets read."}
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
