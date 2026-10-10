#!/usr/bin/env python3
"""Final scientific plots, full tables and first-in-manifest matched examples."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from frozen_package import digest,validate_package

STYLE={'net_benefit':('Benefit minus harm','#c23b34','o'),
       'trained_A_error':('A-error predictor','#277da8','s'),
       'gap':('Top1-top2 gap','#d58b12','^'),
       'rescue_only':('Rescue only','#398257','D'),
       'net_benefit_no_std':('Benefit without std','#8169a7','v')}


def read(path):return json.loads(path.read_text())


def save(fig,out,name):
    fig.savefig(out/(name+'.pdf'),bbox_inches='tight',metadata={'Title':name,'Subject':'Frozen final evaluation; no test calibration'})
    fig.savefig(out/(name+'.png'),bbox_inches='tight',dpi=220)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    package=validate_package(args.package)
    acceptance=read(args.run_dir/'phase_acceptance.json');assert acceptance['passed']
    for name,sha in acceptance['source_sha256'].items():assert digest(args.run_dir/name)==sha
    args.output.mkdir()
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    pairs={};table=[]
    for dataset,config in package['evaluation_plan']['datasets'].items():
        for second in ['eigenplaces','dinov2']:
            folder=args.run_dir/'results'/dataset/('pair_'+second)
            acc=read(folder/'accuracy.json');lat=read(folder/'latency.json')['policies']
            dev=read(args.package.parent/package['files'][second+'_development_metrics']['path'])['splits']['validation']
            pairs[(dataset,second)]={'accuracy':acc,'latency':lat,'development':dev}
            for radius,policies in acc['by_radius'].items():
                for name,v in policies.items():
                    timed=lat.get(name,{}) if int(radius)==config['primary_radius'] else {}
                    table.append({'dataset':dataset,'second_encoder':second,'radius_frames':int(radius),
                        'primary':int(radius)==config['primary_radius'],'policy':name,**v,
                        'mean_ms':timed.get('mean_ms'),'median_ms':timed.get('median_ms'),'p95_ms':timed.get('p95_ms'),
                        'peak_torch_cuda_allocated_bytes':timed.get('peak_torch_cuda_allocated_bytes')})
    keys=list(dict.fromkeys(k for row in table for k in row))
    with (args.output/'all_final_metrics.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(table)
    fig,axes=plt.subplots(2,2,figsize=(10,7),squeeze=False)
    for col,dataset in enumerate(['nordland','gardens']):
        for row,second in enumerate(['eigenplaces','dinov2']):
            ax=axes[row,col];data=pairs[(dataset,second)];radius=str(data['accuracy']['primary_radius'])
            primary=data['accuracy']['by_radius'][radius];lat=data['latency']
            for family,(label,color,marker) in STYLE.items():
                budgets=[10,25,50] if family in ['net_benefit','trained_A_error'] else [25]
                names=[f'{family}_budget{b:02d}' for b in budgets]
                ax.plot([lat[n]['mean_ms'] for n in names],[100*primary[n]['R@1'] for n in names],
                    marker=marker,color=color,label=label,linewidth=1.2)
                for n,b in zip(names,budgets):
                    if family=='net_benefit' and second=='eigenplaces':
                        ax.annotate(str(b),(lat[n]['mean_ms'],100*primary[n]['R@1']),xytext=(3,4),textcoords='offset points',fontsize=7)
            for family,marker,color in [('random_budget','x','#777777'),('random_matched_net','+','#222222')]:
                names=[f'{family}_budget25_seed{s}' for s in range(5)]
                ax.scatter([lat[n]['mean_ms'] for n in names],[100*primary[n]['R@1'] for n in names],marker=marker,color=color,s=30,label=family.replace('_',' '))
            for name,marker,color in [('A_only','*','#161616'),('B_only','P','#a755a1')]:
                ax.scatter(lat[name]['mean_ms'],100*primary[name]['R@1'],marker=marker,color=color,s=85,label=name.replace('_',' '))
            ax.set_title(f'{dataset.title()}, B={second}: frozen final test')
            ax.set_xlabel('Measured full-query mean latency (ms)');ax.set_ylabel('Recall@1 (%)');ax.grid(alpha=.18)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8)
    fig.suptitle('Nominal budgets are validation settings; final invocation fractions differ\nBenefit/error: 10/25/50% settings; other conditional points: 25%',fontsize=10)
    fig.tight_layout(rect=(0,.115,1,.935));save(fig,args.output,'final_accuracy_latency')
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),squeeze=False)
    for col,second in enumerate(['eigenplaces','dinov2']):
        ax=axes[0,col]
        for dataset,line in [('nordland','-'),('gardens','--')]:
            data=pairs[(dataset,second)];primary=data['accuracy']['by_radius'][str(data['accuracy']['primary_radius'])]
            for family,(label,color,_) in list(STYLE.items())[:3]:
                ax.plot([10,25,50],[100*primary[f'{family}_budget{b:02d}']['invocation_fraction'] for b in [10,25,50]],
                    line,marker='o',color=color,label=dataset.title()+': '+label)
        ax.plot([0,100],[0,100],':',color='#999999',label='nominal reference')
        ax.set(xlim=(0,55),ylim=(-2,103),xlabel='Validation budget (%)',ylabel='Actual final B invocation (%)',title='B='+second)
        ax.grid(alpha=.18)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=7)
    fig.tight_layout(rect=(0,.22,1,1));save(fig,args.output,'final_invocation_drift')
    fig,axes=plt.subplots(1,2,figsize=(9,3.5))
    complementarity={}
    for ax,dataset in zip(axes,['nordland','gardens']):
        counts=acceptance['outcomes'][dataset+'_eigenplaces'];complementarity[dataset]=counts
        matrix=np.array([[counts['both_right'],counts['harm']],[counts['rescue'],counts['both_wrong']]])
        ax.imshow(matrix,cmap='Blues',vmin=0,vmax=package['evaluation_plan']['datasets'][dataset]['queries'])
        for (i,j),n in np.ndenumerate(matrix):ax.text(j,i,str(n),ha='center',va='center',fontsize=16,color='white' if n>matrix.max()*.6 else '#111111')
        ax.set_xticks([0,1],['Eigen right','Eigen wrong']);ax.set_yticks([0,1],['A right','A wrong']);ax.set_title(dataset.title()+': all final queries')
    fig.tight_layout();save(fig,args.output,'final_complementarity')
    examples=[]
    for dataset in ['nordland','gardens']:
        config=package['evaluation_plan']['datasets'][dataset]
        manifest=read(args.package.parent/package['files'][dataset+'_manifest']['path'])
        lookup={r['image_id']:r for r in manifest['records']}
        gallery={r['frame_index']:r for r in manifest['records'] if r['split']=='gallery'}
        folder=args.run_dir/'results'/dataset/'pair_eigenplaces'
        rows=list(csv.DictReader((folder/'accuracy_per_query.csv').open()))
        by_policy={p:{r['query_image_id']:r for r in rows if r['policy']==p} for p in ['A_only','B_only','net_benefit_budget25']}
        candidates=list(by_policy['A_only'].values())
        model_arrays={};qindices={};dindices={}
        for model in ['cosplace','eigenplaces']:
            directory=args.run_dir/'results'/dataset/model
            qids=read(directory/(config['query_role']+'_image_ids.json'));dids=read(directory/'gallery_image_ids.json')
            qindices[model]={v:i for i,v in enumerate(qids)};dindices[model]={v:i for i,v in enumerate(dids)}
            model_arrays[model]={'query':np.load(directory/(config['query_role']+'_descriptors.npy'),allow_pickle=False),
                'gallery':np.load(directory/'gallery_descriptors.npy',allow_pickle=False)}
        for category,(a,b) in {'both_right':(True,True),'rescue':(False,True),'harm':(True,False),'both_wrong':(False,False)}.items():
            match=next((r for r in candidates if (r['A_correct']=='True')==a and (r['B_correct']=='True')==b),None)
            if match is None:
                examples.append({'dataset':dataset,'category':category,'available':False});continue
            image_id=match['query_image_id'];query=lookup[image_id];chosen=by_policy['net_benefit_budget25'][image_id]
            image_ids=[image_id,gallery[query['frame_index']]['image_id'],
                json.loads(match['top10_image_ids'])[0],json.loads(by_policy['B_only'][image_id]['top10_image_ids'])[0]]
            fig,axes=plt.subplots(1,4,figsize=(12,2.6))
            for ax,selected,label in zip(axes,image_ids,['Query','Aligned reference','A top1','Eigen top1']):
                item=lookup[selected];path=ROOT/item['relative_path'];assert digest(path)==item['sha256']
                with Image.open(path) as im:ax.imshow(im.convert('RGB'))
                ax.set_title(label+'\nframe '+str(item['frame_index']),fontsize=9);ax.axis('off')
            name=f'example_{dataset}_{category}'
            fig.suptitle(f'{dataset}: first {category} in manifest; radius={config["primary_radius"]}; net25 invokes B={chosen["invoked_B"]}',fontsize=10)
            fig.tight_layout();save(fig,args.output,name)
            numerical={}
            for model,policy in [('cosplace','A_only'),('eigenplaces','B_only')]:
                vector=model_arrays[model]['query'][qindices[model][image_id]]
                unit=vector.astype(np.float64);unit/=np.linalg.norm(unit)
                database=model_arrays[model]['gallery'].astype(np.float64)
                database/=np.linalg.norm(database,axis=1,keepdims=True)
                score=np.clip(database@unit,-1,1)
                top_ids=json.loads(by_policy[policy][image_id]['top10_image_ids'])
                numerical[model]={'output_shape':[1,len(vector)],'descriptor_first8':vector[:8].tolist(),
                    'descriptor_l2_norm':float(np.linalg.norm(vector)),
                    'top10_cosine_similarity':[float(score[dindices[model][v]]) for v in top_ids]}
            examples.append({'dataset':dataset,'category':category,'available':True,'selection_rule':'First query in fixed manifest order satisfying this correctness class',
                'query_image_id':image_id,'image_ids':image_ids,'net25_invoked_B':chosen['invoked_B']=='True','net25_gate_score':float(chosen['gate_score']),
                'top10_A':json.loads(match['top10_image_ids']),'top10_B':json.loads(by_policy['B_only'][image_id]['top10_image_ids']),
                'radius_frames':config['primary_radius'],'figure':name+'.png','model_output_and_sorted_scores':numerical})
    (args.output/'matching_examples.json').write_text(json.dumps(examples,indent=2)+'\n')
    meta={'scope':'Frozen final evaluation only; all policies retained','package_sha256':digest(args.package),
        'acceptance_sha256':digest(args.run_dir/'phase_acceptance.json'),'script_sha256':digest(Path(__file__)),
        'metric_rows':len(table),'matplotlib':matplotlib.__version__,'numpy':np.__version__,
        'examples_rule':'First manifest-ordered query of each of four correctness classes; no best-looking selection',
        'notes':['All five random seeds plotted; their variation is not a confidence interval.',
                 'Unmeasured latency cells remain empty; no interpolation.','No thresholds or weights fitted on final data.'],
        'output_sha256':{p.name:digest(p) for p in sorted(args.output.iterdir()) if p.is_file()}}
    (args.output/'figure_provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({k:v for k,v in meta.items() if k!='output_sha256'},indent=2))


if __name__=='__main__':main()
