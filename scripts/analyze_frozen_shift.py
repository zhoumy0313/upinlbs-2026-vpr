#!/usr/bin/env python3
"""Post-hoc descriptive shift audit. No exclusion, fitting or calibration."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from frozen_package import digest,validate_package


def read(path):return json.loads(path.read_text())


def features(queries,gallery):
    q=queries.astype(np.float64);d=gallery.astype(np.float64)
    q/=np.linalg.norm(q,axis=1,keepdims=True);d/=np.linalg.norm(d,axis=1,keepdims=True)
    scores=np.clip(q@d.T,-1,1);ranks=np.argsort(-scores,axis=1,kind='stable')[:,:10]
    top=np.take_along_axis(scores,ranks,axis=1)
    return np.column_stack([top[:,0],top[:,0]-top[:,1],top[:,0]-top[:,4],top.mean(axis=1),top.std(axis=1)])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--package',type=Path,required=True)
    args=parser.parse_args();package=validate_package(args.package)
    assert read(args.run_dir/'phase_acceptance.json')['passed']
    manifest=read(args.package.parent/package['files']['nordland_manifest']['path'])
    old=Path(package['files']['eigenplaces_policies']['original']).parents[1]/'cosplace'
    final=args.run_dir/'results/nordland/cosplace'
    sources={};feature_summary={};duplicates={}
    names=['top1_score','top1_minus_top2','top1_minus_top5','top10_mean','top10_std']
    gpath=final/'gallery_descriptors.npy';gallery=np.load(gpath,allow_pickle=False);sources[str(gpath)]=digest(gpath)
    old_gallery=np.load(old/'gallery_descriptors.npy',allow_pickle=False)
    np.testing.assert_array_equal(gallery,old_gallery)
    for split,count in [('train',600),('validation',300),('test',650)]:
        directory=final if split=='test' else old
        qpath=directory/(split+'_descriptors.npy');qids=read(directory/(split+'_image_ids.json'))
        rows=[r for r in manifest['records'] if r['split']==split]
        assert qids==[r['image_id'] for r in rows] and len(qids)==count
        queries=np.load(qpath,allow_pickle=False);sources[str(qpath)]=digest(qpath)
        assert queries.dtype==np.float32 and queries.shape==(count,512) and np.isfinite(queries).all()
        x=features(queries,gallery)
        feature_summary[split]={n:{'mean':float(x[:,i].mean()),'std_population':float(x[:,i].std()),
            'quantiles_0_25_50_75_100':np.quantile(x[:,i],[0,.25,.5,.75,1]).tolist()} for i,n in enumerate(names)}
        counts=Counter(r['sha256'] for r in rows)
        duplicates[split]={'queries':count,'unique_image_hashes':len(counts),'duplicate_groups':sum(v>1 for v in counts.values()),
            'queries_in_duplicate_groups':sum(v for v in counts.values() if v>1),'extra_duplicate_copies':sum(v-1 for v in counts.values())}
    gardens=read(args.package.parent/package['files']['gardens_manifest']['path'])
    rows=[r for r in gardens['records'] if r['split']=='external_test'];counts=Counter(r['sha256'] for r in rows)
    duplicates['gardens_external_test']={'queries':len(rows),'unique_image_hashes':len(counts),
        'duplicate_groups':sum(v>1 for v in counts.values()),'queries_in_duplicate_groups':sum(v for v in counts.values() if v>1),
        'extra_duplicate_copies':sum(v-1 for v in counts.values())}
    opportunity={}
    for second in ['eigenplaces','dinov2']:
        development=read(args.package.parent/package['files'][second+'_development_metrics']['path'])['splits']['validation']
        opportunity[second]={'validation':{'rescue_opportunities':development['B_only']['rescues'],
            'harm_opportunities':development['B_only']['harms'],'queries':300}}
        for dataset in ['nordland','gardens']:
            acc=read(args.run_dir/'results'/dataset/('pair_'+second)/'accuracy.json')
            p=acc['by_radius'][str(acc['primary_radius'])];b=p['B_only']
            opportunity[second][dataset]={'rescue_opportunities':b['rescues'],'harm_opportunities':b['harms'],'queries':b['n_queries'],
                'actual_calls_by_nominal_budget':{f'{family}_{budget}':p[f'{family}_budget{budget:02d}']['invocation_fraction']
                    for family in ['net_benefit','trained_A_error','gap'] for budget in [10,25,50]}}
    result={'scope':'Post-hoc descriptive diagnostics, not a new test selection rule','no_refitting_or_threshold_change':True,
        'no_duplicate_removed_or_reweighted':True,'frozen_A_gallery_exactly_equals_development_gallery':True,
        'duplicate_hash_counts':duplicates,'A_only_feature_distributions':feature_summary,'opportunities_and_invocation':opportunity,
        'source_sha256':sources,'package_sha256':digest(args.package),
        'interpretation_limit':'Associations describe distribution shift; neither duplicates nor feature differences establish a causal explanation alone.'}
    with (args.run_dir/'shift_diagnostics.json').open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()
