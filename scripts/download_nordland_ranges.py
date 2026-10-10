#!/usr/bin/env python3
"""Resume official Nordland ZIP through bounded HTTP ranges, then verify MD5."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import time

import requests

URL = "https://zenodo.org/records/4016653/files/nordland-part-2020.zip?download=1"
SIZE = 985423099  # Verified from official HTTP Content-Range and metadata.
MD5 = "3127c5965bd4d1f3a1ef8ee49285fbb9"
ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/downloads/nordland-part-2020.zip"
PARTS = ROOT / "data/downloads/nordland-parts"


def md5(path):
    h = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(part):
    index, start, end = part
    path = PARTS / f"{index:02d}.part"
    expected = end - start + 1
    for attempt in range(12):
        have = path.stat().st_size if path.exists() else 0
        if have == expected:
            return path
        if have > expected:
            raise ValueError("Part exceeds declared range")
        position = start + have
        try:
            # Preserve existing proxy settings. Never log response cookies/redirect tokens.
            with requests.get(URL, headers={"Range": f"bytes={position}-{end}"},
                              stream=True, timeout=(20, 60)) as response:
                response.raise_for_status()
                expected_range = f"bytes {position}-{end}/{SIZE}"
                if response.status_code != 206 or response.headers.get("Content-Range") != expected_range:
                    raise ValueError("Server did not honor exact byte range")
                with path.open("ab") as stream:
                    for block in response.iter_content(256 * 1024):
                        if block:
                            if stream.tell() + len(block) > expected:
                                raise ValueError("Response exceeds range")
                            stream.write(block)
            print(json.dumps({"part": index, "bytes": path.stat().st_size, "expected": expected}), flush=True)
        except requests.RequestException as exc:
            print(json.dumps({"part": index, "attempt": attempt + 1,
                              "error_type": type(exc).__name__, "retained_bytes": path.stat().st_size if path.exists() else 0}), flush=True)
            time.sleep(min(attempt + 1, 10))
    raise RuntimeError(f"Part {index} did not complete")


def main():
    if TARGET.exists() and TARGET.stat().st_size == SIZE and md5(TARGET) == MD5:
        print("Official archive already verified")
        return
    PARTS.mkdir(parents=True, exist_ok=True)
    count = 6
    step = (SIZE + count - 1) // count
    ranges = [(i, i * step, min((i + 1) * step - 1, SIZE - 1)) for i in range(count)]
    if TARGET.exists():
        retained = PARTS / "initial_single_stream.partial"
        if retained.exists():
            raise ValueError("Existing partial backup; do not overwrite")
        TARGET.rename(retained)
        first = PARTS / "00.part"
        if not first.exists():
            with retained.open("rb") as source, first.open("xb") as dest:
                dest.write(source.read(min(step, retained.stat().st_size)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
        paths = list(pool.map(download, ranges))
    assembled = PARTS / "assembled.zip"
    with assembled.open("wb") as dest:
        for path in paths:
            with path.open("rb") as source:
                shutil.copyfileobj(source, dest, 1024 * 1024)
    actual = md5(assembled)
    assert assembled.stat().st_size == SIZE and actual == MD5, "Official checksum mismatch; retain parts"
    assembled.rename(TARGET)
    print(json.dumps({"archive": str(TARGET), "bytes": SIZE, "md5": actual, "official_md5_matches": True}))


if __name__ == "__main__":
    main()
