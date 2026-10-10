"""Owned static scientific plots from immutable tables; no dataset photo redistribution."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .runtime import ROOT,Run,state,sha

def main():
    st=state();run=Run('g6_scientific_figures','reproducible numeric scientific panels',dict(dataset_photos_excluded=True));print(run.id,flush=True);g1=ROOT/'outputs_v3'/st['g1_run'];a=json.loads((g1/'raw_metrics.json').read_text());public=ROOT/'artifacts/v3/figures';public.mkdir(exist_ok=False)
    coverage=[r for r in a['coverage'] if r['dataset']=='St_Lucia' and r['split']=='descriptive' and r['radius']==10 and r['H']==1];radii=[x['r'] for x in coverage];fig,ax=plt.subplots(figsize=(4.8,2.8));ax.plot(radii,[100*x['error_coverage'] for x in coverage],'o-',label='Diagnostic candidate oracle');ax.plot(radii,[100*x['random_error_coverage'] for x in coverage],'s--',label='Equal-size random pool');ax.set(xlabel='Reference-index radius r (not metres)',ylabel='Coverage among 372 T errors (%)',ylim=(0,105),xticks=radii);ax.legend(fontsize=8);fig.tight_layout()
    for ext in ['pdf','png','svg']:fig.savefig(public/('candidate_coverage.'+ext),dpi=180)
    plt.close(fig)
    rows=[r for r in a['results'] if r['dataset']=='St_Lucia' and r['split']=='descriptive' and r['method'] in ['A','fixed_L9','full_L3','full_L5','full_L9'] and r['radius'] in [10,25]];fig,ax=plt.subplots(figsize=(4.8,2.8))
    for method in ['A','fixed_L9','full_L3','full_L5','full_L9']:
        values=sorted([r for r in rows if r['method']==method],key=lambda r:r['radius']);ax.plot([r['radius'] for r in values],[100*r['recall']['1'] for r in values],'o-',label=method)
    ax.set(xlabel='Geographic label radius (m)',ylabel='Seen-stream R@1 (%)',xticks=[10,25]);ax.legend(fontsize=8);fig.tight_layout()
    for ext in ['pdf','png','svg']:fig.savefig(public/('strict_vs_wide.'+ext),dpi=180)
    plt.close(fig)
    pts=json.loads((ROOT/'paper/revisions/v3_r04/figure_data.json').read_text());fig,ax=plt.subplots(figsize=(5,2.7));qids=sorted(next(iter(pts.values())).keys(),key=int);width=.18
    for k,(method,values) in enumerate(pts.items()):ax.bar([i+k*width for i in range(len(qids))],[values[q] for q in qids],width,label=method)
    ax.axhline(10,linestyle='--',color='gray');ax.set(xticks=[i+.27 for i in range(len(qids))],xticklabels=['q'+q for q in qids],ylabel='Reference-label distance (m)');ax.legend(fontsize=8);fig.tight_layout()
    for ext in ['pdf','png','svg']:fig.savefig(public/('real_case_distances.'+ext),dpi=180)
    plt.close(fig);run.write('model_identity.json',dict(not_applicable='Numeric plot generation only'));run.write('figure_data.json',dict(coverage=coverage,recall=rows,cases=pts,source_run=st['g1_run'],source_sha256=sha(g1/'raw_metrics.json')));(public/'figure_data.json').write_bytes((run.path/'figure_data.json').read_bytes());(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()));run.finish(dict(files=[p.name for p in public.iterdir()],actual_points_not_synthetic=True),dict(passed=True,source_hashes_retained=True));state(g6_figure_run=run.id)
if __name__=='__main__':main()
