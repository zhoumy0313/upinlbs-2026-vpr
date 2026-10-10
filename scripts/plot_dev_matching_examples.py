#!/usr/bin/env python3
"""First validation query in each outcome class: reproducible diagnostic examples."""
import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--run-dir",type=Path,required=True)
    args=parser.parse_args()
    second=json.loads((args.run_dir/"dev_baselines/metrics.json").read_text()).get("B_method","dinov2")
    second_title={"dinov2":"DINOv2","eigenplaces":"EigenPlaces"}[second]
    records=json.loads(args.manifest.read_text())["records"]
    lookup={r["image_id"]:r for r in records}
    gallery={r["frame_index"]:r for r in records if r["traverse"]=="summer"}
    rows=list(csv.DictReader((args.run_dir/"dev_baselines/validation_per_query.csv").open()))
    classes=["both_right","A_wrong_B_right","A_right_B_wrong","both_wrong"]
    chosen=[next((r for r in rows if r["outcome"]==key),None) for key in classes]
    chosen=[r for r in chosen if r is not None]
    font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",15)
    canvas=Image.new("RGB",(1720,310*len(chosen)+36),"white")
    draw=ImageDraw.Draw(canvas)
    for i,row in enumerate(chosen):
        assert row["split"]=="validation" and lookup[row["query_image_id"]]["split"]=="validation"
        q=lookup[row["query_image_id"]]
        panels=[("Winter query",q,None), ("Summer same-frame anchor",gallery[q["frame_index"]],None),
                ("A: CosPlace top1",lookup[row["A_top1_image_id"]],row["A_correct"]=="True"),
                (f"B: {second_title} top1",lookup[row["B_top1_image_id"]],row["B_correct"]=="True")]
        draw.text((8,i*310+5),f"{row['outcome']} | validation frame {q['frame_index']} | positives: frame difference <= 5",font=font,fill="black")
        for column,(title,record,correct) in enumerate(panels):
            x,y=column*430+8,i*310+38
            draw.text((x,y),title,font=font,fill="black")
            label=f"{Path(record['relative_path']).name} | frame {record['frame_index']}"
            if correct is not None:
                label+=f" | {'hit' if correct else 'miss'}"
            draw.text((x,y+22),label,font=font,fill="black")
            with Image.open(ROOT/record["relative_path"]) as image:
                panel=ImageOps.contain(image.convert("RGB"),(412,220))
                canvas.paste(panel,(x,y+48))
            if correct is not None:
                draw.rectangle((x,y+48,x+panel.width,y+48+panel.height),outline="green" if correct else "red",width=4)
    draw.text((8,canvas.height-28),"Development only; first query per outcome, fixed order. No gate, no final-test examples.",font=font,fill="black")
    canvas.save(args.run_dir/"dev_matching_examples.jpg")
    with (args.run_dir/"dev_matching_examples.json").open("x") as stream:
        json.dump({"selection_rule":"first validation query in ascending manifest order per outcome class",
                   "query_ids":[r["query_image_id"] for r in chosen],"rows":chosen},stream,indent=2)
    print(args.run_dir/"dev_matching_examples.jpg")


if __name__=="__main__":main()
