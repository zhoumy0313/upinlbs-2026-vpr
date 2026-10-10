#!/usr/bin/env python3
"""P1 raw image contact sheet with IDs; never computes model predictions."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text())
    records = payload["records"]
    dataset = records[0]["dataset"]
    db, queries = ("summer", "winter") if dataset == "nordland" else ("day_right", "night_right")
    by_key = {(r["traverse"], r["frame_index"]): r for r in records}
    indexes = [1, 350, 700, 1000, 1750] if dataset == "nordland" else [1, 50, 100, 150, 200]
    canvas = Image.new("RGB", (920, 270 * len(indexes)), "white")
    draw = ImageDraw.Draw(canvas)
    for rownum, frame in enumerate(indexes):
        for column, traverse in enumerate([db, queries]):
            row = by_key[(traverse, frame)]
            with Image.open(ROOT / row["relative_path"]) as image:
                panel = ImageOps.contain(image.convert("RGB"), (450, 225))
                canvas.paste(panel, (column * 460, rownum * 270 + 40))
            label = f"frame {frame} | {traverse} | {Path(row['relative_path']).name}"
            draw.text((column * 460 + 5, rownum * 270 + 8), label, fill="black")
    draw.text((5, canvas.height - 12), "Raw alignment inspection only; no model predictions or final-test metrics", fill="black")
    canvas.save(args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
