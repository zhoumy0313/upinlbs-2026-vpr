"""Scientific plots of actual baseline counts, not a publication-ready test claim."""
import argparse
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_helpers import baseline_plot_points
from runtime import digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--metrics',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    m=json.loads(a.metrics.read_text());points=baseline_plot_points(m)
    a.out.mkdir(parents=True,exist_ok=False)
    fig,ax=plt.subplots(figsize=(6.6,3.5))
    for length in [1,3,5,9]:
        rows=sorted([r for r in points if r['length']==length],key=lambda r:r['weight'])
        ax.plot([r['weight'] for r in rows],[100*r['R1'] for r in rows],marker='o',label=f'L={length}')
    for name in ['A-only','B-only','RRF_k60']:
        row=next(r for r in m['results'] if r['split']=='validation' and r['method']==name)
        ax.axhline(100*row['common']['R@1']['recall'],linestyle='--',alpha=.65,label=name)
    ax.set(xlabel='Fixed temporal weight',ylabel='Recall@1 (%)',title='Development validation: identical 292 queries',xticks=[0,.25,.5,.75,1])
    ax.legend(ncol=3,fontsize=8);ax.grid(alpha=.2);fig.tight_layout()
    for suffix in ['png','pdf']:fig.savefig(a.out/f'fixed_temporal_grid.{suffix}',dpi=180)
    with (a.out/'figure_points.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(points[0])+['metrics_sha256']);w.writeheader()
        w.writerows([{**r,'metrics_sha256':digest(a.metrics)} for r in points])
    plt.close(fig)
    print(json.dumps({'plot_points':len(points),'input_sha256':digest(a.metrics),'output':str(a.out)}))

if __name__=='__main__':main()
