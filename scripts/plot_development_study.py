#!/usr/bin/env python3
"""Publication figures from verified development outputs, never final results."""
import argparse
import csv
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from frozen_package import digest,validate_package


STYLE={"net_benefit":("Benefit minus harm","#c23b34","o"),
       "trained_A_error":("A-error predictor","#277da8","s"),
       "gap":("Top1-top2 gap","#d58b12","^"),
       "rescue_only":("Rescue head only","#398257","D"),
       "net_benefit_no_std":("Benefit without std","#8169a7","v")}


def save(fig,out,name):
    fig.savefig(out/(name+".pdf"),bbox_inches="tight",metadata={"Title":name,"Subject":"Development validation only; not final evaluation"})
    fig.savefig(out/(name+".png"),dpi=220,bbox_inches="tight")
    plt.close(fig)


def verified_latency(path):
    value=json.loads((path/"metrics.json").read_text())
    assert value["real_model_forwards"] and not value["cached_query_used_inside_timed_path"]
    records=list(csv.DictReader((path/"per_query.csv").open()))
    assert len(records)==17*300*3
    for name,entry in value["policies"].items():
        rows=[r for r in records if r["policy"]==name]
        times=np.array([float(r["total_ms"]) for r in rows])
        assert len(rows)==entry["n_queries"]==900
        assert entry["B_forward_calls"]==sum(r["invoked_B"]=="True" for r in rows)
        assert entry["A_forward_calls"]==(0 if name=="B_only" else 900)
        np.testing.assert_allclose([entry["mean_ms"],entry["median_ms"],entry["p95_ms"]],
                                  [times.mean(),np.median(times),np.percentile(times,95)],atol=1e-12)
    return value["policies"]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--package",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    package=validate_package(args.package,require_confirmation=False)
    args.output.mkdir()
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,
                         "pdf.fonttype":42,"ps.fonttype":42,"text.usetex":False})
    pairs={};sources={};points=[]
    for method in ["dinov2","eigenplaces"]:
        entry=package["files"][method+"_development_metrics"]
        path=args.package.parent/entry["path"]
        result=json.loads(path.read_text());assert result["development_only"] and not result["final_test_used"]
        metrics=result["splits"]["validation"]
        assert metrics["A_only"]["n_queries"]==300
        for item in metrics.values():
            assert item["R@1"]<=item["R@5"]<=item["R@10"]
            np.testing.assert_allclose(item["R@1"]-metrics["A_only"]["R@1"],(item["rescues"]-item["harms"])/300,atol=1e-14)
        run=Path(package["files"][method+"_policies"]["original"]).parents[1]
        latency_path=run/"online_validation_budget25"
        latency=verified_latency(latency_path)
        pairs[method]={"metrics":metrics,"random":result["random_all_seeds_summary"]["validation"],"latency":latency}
        sources[method]={"development_metrics_sha256":digest(path),"latency_metrics_sha256":digest(latency_path/"metrics.json"),
                         "latency_rows_sha256":digest(latency_path/"per_query.csv"),"latency_rows_checked":15300}
        for name,m in metrics.items():
            if name=="oracle_DIAGNOSTIC_ONLY":continue
            points.append({"pair":method,"policy":name,"R1_percent":m["R@1"]*100,"invocation_percent":m["invocation_fraction"]*100,
                           "rescues":m["rescues"],"harms":m["harms"],"mean_ms":latency[name]["mean_ms"] if name in latency else None})
    titles={"dinov2":"A: CosPlace / B: DINOv2 CLS","eigenplaces":"A: CosPlace / B: EigenPlaces"}
    fig,axes=plt.subplots(1,2,figsize=(9.5,3.6),sharey=True)
    for ax,(method,data) in zip(axes,pairs.items()):
        metrics=data["metrics"]
        for family,(label,color,marker) in STYLE.items():
            values=[metrics[f"{family}_budget{b}"] for b in [10,25,50]]
            ax.plot([v["invocation_fraction"]*100 for v in values],[v["R@1"]*100 for v in values],
                    color=color,marker=marker,label=label,linewidth=1.4,markersize=5)
        random=[data["random"][f"random_budget_budget{b}"] for b in [10,25,50]]
        ax.errorbar([v["invocation_fraction"]["mean"]*100 for v in random],[v["R@1"]["mean"]*100 for v in random],
                    yerr=[v["R@1"]["std_population"]*100 for v in random],color="#777777",marker="x",linestyle="--",capsize=3,label="Random (5 seeds, mean +/- SD)")
        ax.scatter([0,100],[metrics["A_only"]["R@1"]*100,metrics["B_only"]["R@1"]*100],color="black",marker="*",s=65,label="Single-encoder endpoints",zorder=4)
        if method=="dinov2":ax.annotate("Benefit: zero calls at all caps",xy=(0,metrics["A_only"]["R@1"]*100),xytext=(12,78),arrowprops={"arrowstyle":"->","color":"#c23b34"},fontsize=8)
        ax.set(title=titles[method],xlabel="Actual validation B invocation (%)",xlim=(-4,105),ylim=(45,89))
        ax.grid(alpha=.2);ax.set_xticks([0,10,25,50,100])
    axes[0].set_ylabel("Validation Recall@1 (%)")
    axes[1].legend(fontsize=7,loc="lower right")
    fig.suptitle("Development only: Nordland-Part-2020, 300 queries, radius 5",fontsize=10)
    fig.tight_layout();save(fig,args.output,"development_accuracy_invocation")

    fig,axes=plt.subplots(1,2,figsize=(8.8,3.6))
    outcomes={}
    for ax,(method,data) in zip(axes,pairs.items()):
        metrics=data["metrics"];b=metrics["B_only"]
        a_correct=round(metrics["A_only"]["R@1"]*300)
        count={"both_right":a_correct-b["harms"],"harm":b["harms"],"rescue":b["rescues"],"both_wrong":300-a_correct-b["rescues"]}
        assert sum(count.values())==300;outcomes[method]=count
        matrix=np.array([[count["both_right"],count["harm"]],[count["rescue"],count["both_wrong"]]])
        ax.imshow(matrix,cmap="Blues",vmin=0,vmax=200)
        labels=[["Both correct","Harm opportunity"],["Rescue opportunity","Both wrong"]]
        for i in range(2):
            for j in range(2):ax.text(j,i,f"{labels[i][j]}\n{matrix[i,j]} / 300",ha="center",va="center",color="white" if matrix[i,j]>110 else "black",fontsize=9)
        ax.set_xticks([0,1],["B correct","B wrong"]);ax.set_yticks([0,1],["A correct","A wrong"])
        ax.set_title(titles[method],fontsize=9)
    fig.suptitle("Development top1 complementarity; all queries retained",fontsize=10)
    fig.tight_layout();save(fig,args.output,"development_complementarity")

    fig,axes=plt.subplots(1,2,figsize=(9.5,3.7),sharey=True)
    for ax,(method,data) in zip(axes,pairs.items()):
        metrics,latency=data["metrics"],data["latency"]
        for name,label,marker in [("A_only","A only","*"),("B_only","B only","P")]:
            ax.scatter(latency[name]["mean_ms"],metrics[name]["R@1"]*100,color="black",marker=marker,s=65,label=label,zorder=5)
        for family,(label,color,marker) in STYLE.items():
            name=family+"_budget25"
            ax.scatter(latency[name]["mean_ms"],metrics[name]["R@1"]*100,label=label,color=color,marker=marker,s=45)
        for family,label,color in [("random_budget","Random 25% cap","#888888"),("random_matched_net","Random matched to benefit","#bb9e7b")]:
            keys=[f"{family}_budget25_seed{s}" for s in range(5)]
            ax.scatter([latency[n]["mean_ms"] for n in keys],[metrics[n]["R@1"]*100 for n in keys],marker="x",s=30,color=color,label=label)
        ax.set(title=titles[method],xlabel="Measured mean batch1 query latency (ms)",ylim=(45,89))
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Validation Recall@1 (%)")
    axes[1].legend(fontsize=6.5,loc="lower right")
    fig.suptitle("Development only: actual encoders; 300 queries x 3 passes per policy",fontsize=10)
    fig.text(.5,.005,"Conditional points use the 25% validation cap; original benefit actually invokes B 0%. GPU clocks unlocked.",ha="center",fontsize=7)
    fig.tight_layout(rect=[0,.035,1,1]);save(fig,args.output,"development_accuracy_latency")
    with (args.output/"plot_points.csv").open("x",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(points[0]));writer.writeheader();writer.writerows(points)
    with (args.output/"figure_provenance.json").open("x") as stream:
        json.dump({"scope":"development only; no final-test reads","source_package_sha256":digest(args.package),"sources":sources,
                   "outcomes":outcomes,"script_sha256":digest(__file__),"matplotlib":matplotlib.__version__,"numpy":np.__version__,
                   "notes":["Random bars are population SD across all five seeds, not confidence intervals.",
                            "Runtime points use measured real forwards; 10/50 latency is absent, never interpolated.",
                            "Multiple benefit caps have identical zero-call points for DINOv2; none discarded from data."],
                   "figure_sha256":{p.name:digest(p) for p in sorted(args.output.iterdir()) if p.suffix in {".pdf",".png",".csv"}}},stream,indent=2)
    print(args.output)


if __name__=="__main__":main()
