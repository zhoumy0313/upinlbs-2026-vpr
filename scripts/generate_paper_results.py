#!/usr/bin/env python3
"""Standalone-compatible LaTeX tables and vector picture from final artifacts."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from frozen_package import digest


def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();acceptance=read(args.run_dir/'phase_acceptance.json');assert acceptance['passed']
    for name,sha in acceptance['source_sha256'].items():assert digest(args.run_dir/name)==sha
    args.output.mkdir()
    data={}
    for dataset in ['nordland','gardens']:
        directory=args.run_dir/'results'/dataset/'pair_eigenplaces'
        acc=read(directory/'accuracy.json')
        data[dataset]={'accuracy':acc['by_radius'][str(acc['primary_radius'])],
            'random':acc['random_all_seeds'],'latency':read(directory/'latency.json')['policies']}
    lines=[r'\begin{table*}[t]',r'\caption{Frozen final evaluation with EigenPlaces as B. Budgets in labels are validation settings; B columns show actual final invocation. Random rows give five-seed means and population SD for R@1. Times are actual full-query means (ms), with unlocked laptop clocks.}',
        r'\label{tab:final}',r'\centering',r'\begin{tabular}{lrrr rrr}',r'\toprule',
        r'&\multicolumn{3}{c}{Nordland holdout ($Q=650$, $r=5$)}&\multicolumn{3}{c}{Gardens Point ($Q=200$, $r=0$)}\\',
        r'Policy & R@1 (\%) & B (\%) & ms & R@1 (\%) & B (\%) & ms\\',r'\midrule']
    rows=[('A-only','A_only'),('EigenPlaces-only','B_only')]
    rows += [(f'Benefit ({b}\\%)',f'net_benefit_budget{b:02d}') for b in [10,25,50]]
    rows += [(f'A-error ({b}\\%)',f'trained_A_error_budget{b:02d}') for b in [10,25,50]]
    rows += [('Gap (25\\%)','gap_budget25'),('Rescue only (25\\%)','rescue_only_budget25'),('Benefit, no std (25\\%)','net_benefit_no_std_budget25')]
    for label,name in rows:
        cells=[]
        for dataset in ['nordland','gardens']:
            d=data[dataset];v=d['accuracy'][name];cells += [f'{100*v["R@1"]:.2f}',f'{100*v["invocation_fraction"]:.2f}',f'{d["latency"][name]["mean_ms"]:.2f}']
        lines.append(label+' & '+' & '.join(cells)+r'\\')
    for family,label in [('random_budget','Random, nominal 25\\%'),('random_matched_net','Random, validation-matched')]:
        cells=[]
        for dataset in ['nordland','gardens']:
            d=data[dataset];prefix=family+'_budget25';v=d['random'][prefix]
            cells += [f'${100*v["R@1"]["mean"]:.2f}\\pm{100*v["R@1"]["std_population"]:.2f}$',
                f'{100*v["invocation_fraction"]["mean"]:.2f}',f'{np.mean([d["latency"][prefix+f"_seed{s}"]["mean_ms"] for s in range(5)]):.2f}']
        lines.append(label+' & '+' & '.join(cells)+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table*}']
    (args.output/'final_table.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\begin{table*}[t]',r'\caption{Single-encoder final Recall@1/5/10 (\%). All use the same declared 224-pixel adaptation; these are not original-paper benchmark reproductions.}',
        r'\label{tab:baselines}',r'\centering',r'\begin{tabular}{lrrr rrr}',r'\toprule',
        r'&\multicolumn{3}{c}{Nordland, $r=5$}&\multicolumn{3}{c}{Gardens Point, $r=0$}\\',
        r'Encoder & R@1 & R@5 & R@10 & R@1 & R@5 & R@10\\',r'\midrule']
    for label,second,name in [('CosPlace R18','eigenplaces','A_only'),('EigenPlaces R50','eigenplaces','B_only'),('DINOv2 ViT-S/14 CLS','dinov2','B_only')]:
        cells=[]
        for dataset in ['nordland','gardens']:
            acc=read(args.run_dir/'results'/dataset/('pair_'+second)/'accuracy.json')
            v=acc['by_radius'][str(acc['primary_radius'])][name]
            cells += [f'{100*v[f"R@{k}"]:.2f}' for k in [1,5,10]]
        lines.append(label+' & '+' & '.join(cells)+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table*}']
    (args.output/'baseline_table.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\begin{figure*}[t]',r'\centering',r'\setlength{\unitlength}{1pt}']
    point_sources={}
    for dataset in ['nordland','gardens']:
        d=data[dataset];acc=d['accuracy'];lat=d['latency']
        selected=[('A_only','A'),('B_only','B')]
        selected += [(f'net_benefit_budget{b:02d}','benefit') for b in [10,25,50]]
        selected += [(f'trained_A_error_budget{b:02d}','error') for b in [10,25,50]]
        selected += [('gap_budget25','gap')]
        selected += [(f'{family}_budget25_seed{s}','random') for family in ['random_budget','random_matched_net'] for s in range(5)]
        points=[(n,kind,lat[n]['mean_ms'],100*acc[n]['R@1']) for n,kind in selected]
        point_sources[dataset]=[{'policy':n,'symbol':kind,'mean_ms':ms,'R@1_percent':r1} for n,kind,ms,r1 in points]
        xmin=min(p[2] for p in points);xmax=max(p[2] for p in points);dx=max(1.,(xmax-xmin)*.10);xmin-=dx;xmax+=dx
        ymin=min(p[3] for p in points);ymax=max(p[3] for p in points);dy=max(1.,(ymax-ymin)*.15);ymin=max(0.,ymin-dy);ymax=min(100.,ymax+dy)
        x=lambda v:36+188*(v-xmin)/(xmax-xmin)
        y=lambda v:29+107*(v-ymin)/(ymax-ymin)
        lines += [r'\begin{picture}(250,167)',r'\linethickness{0.4pt}',r'\put(36,29){\line(1,0){188}}',r'\put(36,29){\line(0,1){107}}',
            r'\put(130,154){\makebox(0,0){\small '+('Nordland holdout' if dataset=='nordland' else 'Gardens Point')+r'}}',
            r'\put(130,5){\makebox(0,0){\scriptsize Mean latency (ms)}}',r'\put(25,146){\makebox(0,0)[l]{\scriptsize R@1 (\%)}}']
        for tick in np.linspace(xmin,xmax,4):
            lines.append(f'\\put({x(tick):.2f},26){{\\line(0,1){{3}}}}')
            lines.append(r'\put(%.2f,18){\makebox(0,0){\scriptsize %.1f}}' % (x(tick),tick))
        for tick in np.linspace(ymin,ymax,4):
            lines.append(f'\\put(33,{y(tick):.2f}){{\\line(1,0){{3}}}}')
            lines.append(r'\put(29,%.2f){\makebox(0,0)[r]{\scriptsize %.1f}}' % (y(tick),tick))
        for name,kind,ms,r1 in points:
            px,py=x(ms),y(r1)
            symbol={'A':r'\makebox(0,0){$\star$}','B':r'\makebox(0,0){$+$}',
                'benefit':r'\circle*{3}','error':r'\makebox(0,0){$\square$}',
                'gap':r'\makebox(0,0){$\triangle$}','random':r'\makebox(0,0){\tiny $\times$}'}[kind]
            lines.append(f'\\put({px:.2f},{py:.2f}){{{symbol}}}')
        lines += [r'\end{picture}']
    lines += [r'\caption{Real execution of the EigenPlaces pair: star A-only, plus B-only, filled circles benefit and squares A-error at nominal 10/25/50\%, triangle gap at 25\%, and crosses all five seeds for each random control at 25\%. Each point is measured; unmeasured policies are not interpolated. Actual calls appear in Table~\ref{tab:final}.}',
        r'\label{fig:cost}',r'\end{figure*}']
    (args.output/'cost_figure.tex').write_text('\n'.join(lines)+'\n')
    provenance={'run':str(args.run_dir.resolve()),'acceptance_sha256':digest(args.run_dir/'phase_acceptance.json'),
        'script_sha256':digest(Path(__file__)),'point_sources':point_sources,
        'tex_sha256':{p.name:digest(p) for p in args.output.glob('*.tex')}}
    (args.output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'standalone_vector_figure':True,'points':sum(map(len,point_sources.values()))}))


if __name__=='__main__':main()
