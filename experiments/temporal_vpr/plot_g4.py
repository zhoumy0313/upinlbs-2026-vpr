"""Standalone scientific plots and exact point ledger, using actual frozen evidence."""
import argparse,csv,json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--development',required=True);p.add_argument('--adaptive',required=True)
    p.add_argument('--smr',required=True);p.add_argument('--independent',required=True);p.add_argument('--latency',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);paths={k:Path(getattr(a,k)) for k in ['development','adaptive','smr','independent','latency']}
    data={k:json.loads(v.read_text()) for k,v in paths.items()};points=[]
    methods=['A-only','B-only','RRF_k60','AB_fixed_0.75','fixed_T_best','adaptive_full','SMR_first_filter_adapted']
    best=data['development']['best_temporal_only']['method'];fig,axes=plt.subplots(1,2,figsize=(10,3.3))
    for axis,role in zip(axes,['development','independent']):
        values=[]
        for name in methods:
            key='development' if name not in ['adaptive_full','SMR_first_filter_adapted'] else 'adaptive' if name=='adaptive_full' else 'smr'
            if role=='independent':key='independent'
            actual=best if name=='fixed_T_best' and role=='development' else name
            row=next(r for r in data[key]['results'] if r['method']==actual and (r.get('split')=='validation' if role=='development' else r.get('radius_m')==25))
            cell=row['common']['R@1'];values.append(cell['recall']*100)
            points.append(dict(figure='comparison',role=role,method=name,metric='R@1',correct=cell['correct'],queries=cell['queries'],value_percent=cell['recall']*100,
                source_path=str(paths[key]),source_sha256=sha(paths[key]),json_method=actual))
        axis.bar(range(len(methods)),values,color=['#5975a4','#5f9e6e','#b55d60','#857aab','#8d7866','#d09e73','#808080'])
        axis.set_xticks(range(len(methods)));axis.set_xticklabels(['A','B','RRF','A+B','Fixed T','Adaptive','SMR*'],rotation=30,ha='right')
        axis.set_ylabel('Recall@1 (%)');axis.set_ylim(0,105);axis.grid(axis='y',alpha=.2)
        axis.set_title('Nordland validation (ordinal ±5)' if role=='development' else 'St Lucia independent (UTM ≤25m)')
    fig.tight_layout();fig.savefig(out/'comparison.png',dpi=200);fig.savefig(out/'comparison.pdf');plt.close(fig)
    latency=data['latency']['results'];fig,axis=plt.subplots(figsize=(8,3.3))
    for r in latency:
        for metric in ['mean_ms','median_ms','p95_ms']:
            points.append(dict(figure='latency',role='real-image independent online',method=r['method'],metric=metric,correct='',queries=r['total']['measurements'],
                value_percent=r['total'][metric],source_path=str(paths['latency']),source_sha256=sha(paths['latency']),json_method=r['method']))
    axis.bar(range(len(latency)),[r['total']['median_ms'] for r in latency],color='#5975a4')
    axis.plot(range(len(latency)),[r['total']['p95_ms'] for r in latency],'ko',label='P95')
    axis.set_xticks(range(len(latency)));axis.set_xticklabels([r['method'] for r in latency],rotation=35,ha='right',fontsize=8)
    axis.set_ylabel('Real batch1 latency (ms)');axis.legend();axis.grid(axis='y',alpha=.2);fig.tight_layout()
    fig.savefig(out/'latency.png',dpi=200);fig.savefig(out/'latency.pdf');plt.close(fig)
    with (out/'figure_points.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(points[0]));w.writeheader();w.writerows(points)

if __name__=='__main__':main()
