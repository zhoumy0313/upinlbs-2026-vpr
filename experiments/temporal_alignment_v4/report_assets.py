"""Offline post-test interpretation; never selects or modifies an online method."""
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from runtime import ROOT,write,sha
def main():
    dest=ROOT/'docs/research_v4/figures';dest.mkdir(exist_ok=False)
    summaries=json.loads((ROOT/'docs/research_v4/PROTOCOL_METADATA.json').read_text());dev=json.loads((ROOT/'docs/research_v4/BASELINE_RESULTS.json').read_text());sel=json.loads((ROOT/'configs/v4/selected_methods.json').read_text());test=json.loads((ROOT/'docs/research_v4/INDEPENDENT_RESULTS.json').read_text());state=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text())
    diagnostics=[];pairs=[]
    fig,axes=plt.subplots(1,2,figsize=(8,3.2),constrained_layout=True)
    for ax,seq,label,runid in zip(axes,['freiburg2_pioneer_slam','freiburg3_long_office_household'],['Pioneer (development)','Long Office (independent)'],[state['g3_run'],state['g4_run']]):
        manifest=json.loads((ROOT/'data/manifests/v4'/(seq+'_5Hz_protocol.json')).read_text());g=manifest['g'];q=manifest['q'];gxyz=np.array([r['xyz'] for r in g]);qvalid=[r for r in q if r['valid_gt']];qxyz=np.array([r['xyz'] for r in qvalid]);dist=np.linalg.norm(qxyz[:,None]-gxyz[None,:,:],axis=2);gquat=np.array([r['quaternion_xyzw'] for r in g]);gquat/=np.linalg.norm(gquat,axis=1,keepdims=True);qquat=np.array([r['quaternion_xyzw'] for r in qvalid]);qquat/=np.linalg.norm(qquat,axis=1,keepdims=True);angle=np.degrees(2*np.arccos(np.clip(np.abs(qquat@gquat.T),0,1)));positive=dist<=.5;closed=positive.any(axis=1);min_angle=np.min(np.where(positive,angle,np.inf),axis=1)
        diag=dict(sequence=seq,role='posthoc_offline_diagnosis_not_online_or_selection',radius=.5,closed_queries=int(closed.sum()),best_positive_rotation_degrees_median=float(np.median(min_angle[closed])),positive_rotation_above60deg=int((min_angle[closed]>60).sum()),positive_rotation_above120deg=int((min_angle[closed]>120).sum()),no_orientation_filter=True,no_protocol_or_algorithm_changes=True)
        diagnostics.append(diag)
        ax.plot(gxyz[:,0],gxyz[:,1],label='Fixed earlier gallery',lw=1.3);ax.plot(qxyz[:,0],qxyz[:,1],label='Later queries',lw=1.3);ax.scatter(qxyz[~closed,0],qxyz[~closed,1],s=7,label='No reference within 0.5m',alpha=.4);ax.set_title(label);ax.set_xlabel('Mocap world x (m)');ax.set_ylabel('Mocap world y (m)');ax.axis('equal');ax.legend(fontsize=6)
    fig.savefig(dest/'real_camera_trajectories.pdf');fig.savefig(dest/'real_camera_trajectories.png',dpi=160);plt.close(fig)
    write(ROOT/'docs/research_v4/POSTHOC_DIAGNOSTICS.json',dict(orientation=diagnostics,interpretation='Descriptive metadata diagnosis only; position-only positives can lack aligned views. Does not prove causal origin of model errors or permit test filtering.'))
    fig,ax=plt.subplots(figsize=(5.4,3.2),constrained_layout=True)
    for name,label in [('A','Single CosPlace'),('L3','Index L3'),('L9','Index L9'),('Time_W1.6','Physical-time alignment')]:
        values=[next(m for m in dev['results'] if m['method']==name and m['hz']==hz and m['radius_m']==.5) for hz in [1,3,5]];ax.plot([1,3,5],[100*m['R1'] for m in values],marker='o',label=label)
    ax.set_xlabel('Artificial development sampling (Hz)');ax.set_ylabel('0.5m closed-set R@1 (%)');ax.legend(fontsize=7);ax.grid(alpha=.2);fig.savefig(dest/'sampling_sensitivity.pdf');fig.savefig(dest/'sampling_sensitivity.png',dpi=160);plt.close(fig)
    # Standalone TikZ/pgf-free figure embeds exact coordinates in the manuscript source.
    coords={name:[(hz,100*next(m['R1'] for m in dev['results'] if m['method']==name and m['hz']==hz and m['radius_m']==.5)) for hz in [1,3,5]] for name in ['A','L9','Time_W1.6']}
    commands=[]
    for name,color in [('A','black'),('L9','red'),('Time_W1.6','blue')]:
        points=' -- '.join(f'({.8+(hz-1)*.6:.3f},{.35+val*.12:.3f})' for hz,val in coords[name]);commands.append('\\draw['+color+',thick] '+points+';')
        for hz,val in coords[name]:commands.append(f'\\fill[{color}] ({.8+(hz-1)*.6:.3f},{.35+val*.12:.3f}) circle (1.2pt);')
    source=r'''\begin{figure}[t]\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\draw[->] (0.8,0.35)--(3.55,0.35);\draw[->] (0.8,0.35)--(0.8,2.55);
\node[font=\scriptsize,rotate=90] at (0.15,1.45){0.5m R@1 (percent)};
\node[font=\scriptsize] at (2.15,0.02){Artificial developer sampling (Hz)};
\foreach \x/\label in {0.8/1,2.0/3,3.2/5}{\node[font=\scriptsize] at (\x,0.19){\label};}
\foreach \y/\label in {0.35/0,0.95/5,1.55/10,2.15/15}{\node[font=\scriptsize] at (0.57,\y){\label};}
'''+ '\n'.join(commands)+r'''
\node[font=\scriptsize,text=black] at (4.2,2.05){Single A};
\node[font=\scriptsize,text=red] at (4.2,1.75){Index L9};
\node[font=\scriptsize,text=blue] at (4.2,1.45){Time 1.6s};
\end{tikzpicture}
\caption{Pioneer artificial sampling changes both history duration and gallery coverage. Fixed physical-time alignment is a baseline, not evidence of endpoint-refinement improvement or a new independent collection.}\label{fig:sampling}\end{figure}
'''
    (ROOT/'docs/research_v4/PAPER_FIGURES.tex').write_text(source);write(dest/'figure_data.json',dict(sampling_coordinates=coords,orientation=diagnostics,source_sha256={p.name:sha(p) for p in [ROOT/'docs/research_v4/BASELINE_RESULTS.json',ROOT/'docs/research_v4/PROTOCOL_METADATA.json']}))
    # Paired blocks are exploratory, with original full query order, not iid claims.
    for label,seq,runid in [('development','freiburg2_pioneer_slam',state['g3_run']),('test','freiburg3_long_office_household',state['g4_run'])]:
        rows=[]
        with (ROOT/'outputs_v4'/runid/'per_query.csv').open() as f:
            for row in csv.DictReader(f):
                if row['method']==sel['proposed']['name'] and row['hz']=='5' and float(row['radius_m'])==.5:rows.append(row)
        delta=np.array([int(r['hit1'])-int(r['A_hit1']) for r in rows]);mask=np.array([r['closed']=='1' for r in rows]);bootstrap=[]
        for size in [20,50]:
            rng=np.random.default_rng(0);values=[]
            for _ in range(1000):
                indices=[]
                while len(indices)<len(rows):
                    start=int(rng.integers(0,len(rows)));indices.extend((np.arange(size)+start)%len(rows))
                ii=np.array(indices[:len(rows)]);selected=mask[ii]
                if selected.any():values.append(float(delta[ii][selected].mean()))
            bootstrap.append(dict(block_frames=size,seed=0,replicates=1000,interval_quantiles_025_975=np.quantile(values,[.025,.975]).tolist(),label='exploratory circular consecutive-query blocks, conditional closed denominator; not independent scene significance'))
        pairs.append(dict(sequence=seq,paired_comparator='CosPlace single A',closed_queries=int(mask.sum()),rescue=sum(int(r['rescue']) for r in rows),harm=sum(int(r['harm']) for r in rows),delta=float(delta[mask].mean()),bootstrap=bootstrap))
    write(ROOT/'docs/research_v4/PAIRED_BLOCK_DIAGNOSTICS.json',pairs)
    print(json.dumps(dict(orientation=diagnostics,figures=list(coords),paired= pairs)),flush=True)
if __name__=='__main__':main()
