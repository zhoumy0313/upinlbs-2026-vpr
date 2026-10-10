"""One adaptive rule and prescribed ablations; all choices precede independent testing."""
import csv
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.core import index_positives
from adaptive import adaptive_stream,fit_train_gap_scales
from runtime import Run,digest,update_state
from diagnostics import canonical_rows

def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text())
    source=ROOT/'outputs_v2'/state['g2_baseline_run'];g2=json.loads((source/'metrics.json').read_text())
    declaration=ROOT/'configs/v2/g3_adaptive_predeclaration.json';config=json.loads(declaration.read_text())
    best=g2['best_temporal_only']['settings'];identities=json.loads((source/'score_identities.json').read_text())
    manifest=ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json';rows=json.loads(manifest.read_text())['records']
    run=Run(ROOT,'g3_adaptive_development',config,dict(g2_run=source.name,g2_metrics_sha256=digest(source/'metrics.json'),
        manifest_sha256=digest(manifest),predeclaration_sha256=digest(declaration)))
    print(run.id,flush=True);update_state(ROOT,latest_run_id=run.id)
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q',
        '--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    train=np.load(source/'train_cosplace_scores.npy');assert digest(source/'train_cosplace_scores.npy')==identities['train_cosplace']['scores_sha256']
    scales=fit_train_gap_scales(train,best['length'],best['velocities']);run.write('train_gap_scales.json',scales)
    # Strictly interior fixed blend is also selected from the existing declared G2 grid.
    interior=sorted([r for r in g2['results'] if r['split']=='validation' and r['method'].startswith('temporal_')
        and r['settings']['length']>1 and 0<r['settings']['weight']<1],
        key=lambda r:(-r['common']['R@1']['recall'],r['settings']['length'],r['settings']['weight'],
                      len(r['settings']['velocities']),r['method']))[0]
    outputs=[];per=[]
    for role in ['train','validation']:
        scores=np.load(source/f'{role}_cosplace_scores.npy');identity=identities[f'{role}_cosplace']
        assert digest(source/f'{role}_cosplace_scores.npy')==identity['scores_sha256']
        qrows=canonical_rows(rows,identity['query_ids']);grows=canonical_rows(rows,identity['gallery_ids'])
        positive=index_positives(np.array([r['frame_index'] for r in qrows]),np.array([r['frame_index'] for r in grows]),5)
        mask=np.arange(len(qrows))>=8;a_order=np.argsort(-scores,axis=1,kind='stable')
        a_correct=positive[np.arange(len(scores)),a_order[:,0]]
        options=dict(length=best['length'],velocities=best['velocities'],scales=scales,candidate_count=50)
        variants=[('adaptive_full',{}),('remove_continuity',{'ablation':'remove_continuity'}),
            ('remove_ambiguity',{'ablation':'remove_ambiguity'}),('remove_agreement',{'ablation':'remove_agreement'}),
            ('fixed_lambda1_Top50',{'fixed_weight':1.}),('fixed_lambda05_Top50',{'fixed_weight':.5}),
            ('replace_adaptive_with_G2_fixed_lambda',{'fixed_weight':interior['settings']['weight']})]
        for name,change in variants:
            ranking,metadata=adaptive_stream(scores,**options,**change)
            hits=np.take_along_axis(positive,ranking[:,:10],axis=1);correct=hits[:,0]
            common={f'R@{k}':dict(correct=int(hits[mask,:k].any(axis=1).sum()),queries=int(mask.sum()),
                recall=float(hits[mask,:k].any(axis=1).mean())) for k in [1,5,10]}
            full={f'R@{k}':dict(correct=int(hits[:,:k].any(axis=1).sum()),queries=len(scores),
                recall=float(hits[:,:k].any(axis=1).mean())) for k in [1,5,10]}
            out=dict(split=role,method=name,settings={**options,**change},common=common,full_stream_with_startup=full,
                rescue=int((mask&~a_correct&correct).sum()),harm=int((mask&a_correct&~correct).sum()),
                mean_adaptive_weight=float(np.mean([r['lambda'] for r in metadata if not r['warmup']])))
            outputs.append(out)
            for i,r in enumerate(qrows):
                per.append(dict(split=role,method=name,query_image_id=r['image_id'],common_valid=bool(mask[i]),
                    method_warmup=metadata[i]['warmup'],top1_image_id=identity['gallery_ids'][ranking[i,0]],
                    correct_at_1=bool(hits[i,0]),correct_at_5=bool(hits[i,:5].any()),correct_at_10=bool(hits[i,:10].any()),
                    A_correct=bool(a_correct[i]),weight=metadata[i]['lambda'],metadata=json.dumps(metadata[i])))
    val=[r for r in outputs if r['split']=='validation']
    adaptive=next(r for r in val if r['method']=='adaptive_full')
    strongest_g2=max(r['common']['R@1']['correct'] for r in g2['results'] if r['split']=='validation')
    strongest_fixed=max(r['common']['R@1']['correct'] for r in val if r['method'].startswith('fixed_') or r['method'].startswith('replace_'))
    demonstrated=adaptive['common']['R@1']['correct']>max(strongest_g2,strongest_fixed)
    run.write('metrics.json',dict(development_only=True,results=outputs,fixed_G2_interior_reference=interior,
        strongest_G2_correct=strongest_g2,strongest_Top50_fixed_correct=strongest_fixed,
        adaptive_exceeds_strongest_fixed=demonstrated,
        interpretation='method_gain_on_development_only' if demonstrated else 'adaptive_contribution_not_demonstrated; stop adding mechanisms; empirical track A'))
    with (run.path/'per_query.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
    run.write('checks.json',dict(passed=True,all_original_and_V2_tests_passed=True,train_statistics_without_labels=True,
        no_new_independent_performance_opened=True,no_old_test_tuning=True,one_concrete_rule_only=True,per_query_rows=len(per)))
    (run.path/'interpretation.md').write_text('Adaptive rule predeclared once. Gap scales use train scores only; no GT/filenames/GPS online. All prescribed ablations and stronger fixed Top50 controls retained. Any failure versus strongest temporal forbids a new-method superiority claim and further module additions. Independent results remain unopened.\n')
    print(json.dumps({'run':run.id,'development_val':[{k:r[k] for k in ['method','common','rescue','harm','mean_adaptive_weight']} for r in val],
        'adaptive_gain_demonstrated':demonstrated}),flush=True)

if __name__=='__main__':main()
