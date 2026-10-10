"""Fixed-source SMR first-filter adaptation, train-only fitting and honest abstentions."""
import csv,json,sys,warnings
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.core import index_positives
from diagnostics import canonical_rows
from runtime import Run,digest,update_state
from smr_adapter import official_functions,official_window_features,SmrMatcher

def worker(destination):
    import joblib
    from sklearn import model_selection
    from sklearn.preprocessing import StandardScaler
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import classification_report,confusion_matrix
    from imblearn.over_sampling import SMOTE
    path=Path(destination);state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text())
    data=ROOT/'outputs_v2'/state['g2_baseline_run'];ids=json.loads((data/'score_identities.json').read_text())
    rows=json.loads((ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json').read_text())['records']
    source=official_functions(ROOT,training=True)
    def evaluate_pred(y,folder,pred,tag):
        (path/'training_resampled_diagnostic.json').write_text(json.dumps(dict(
            report=classification_report(y,pred,output_dict=True,zero_division=0),
            confusion=confusion_matrix(y,pred).tolist(),role='training only; not independent CV evidence'),indent=2))
    def plot_mlp_loss(folder,pipeline):
        (path/'mlp_loss.csv').write_text('iteration,training_loss\n'+''.join(f'{i+1},{v}\n' for i,v in enumerate(pipeline.named_steps['mlp'].loss_curve_)))
    source.update(dict(joblib=joblib,model_selection=model_selection,StandardScaler=StandardScaler,
        MLPClassifier=MLPClassifier,Pipeline=Pipeline,ConvergenceWarning=ConvergenceWarning,
        SMOTE=SMOTE,warnings=warnings,evaluate_pred=evaluate_pred,plot_mlp_loss=plot_mlp_loss))
    train=np.load(data/'train_cosplace_scores.npy');assert digest(data/'train_cosplace_scores.npy')==ids['train_cosplace']['scores_sha256']
    q=canonical_rows(rows,ids['train_cosplace']['query_ids']);g=canonical_rows(rows,ids['train_cosplace']['gallery_ids'])
    gt=index_positives(np.array([r['frame_index'] for r in q]),np.array([r['frame_index'] for r in g]),5)
    raw=(2-2*train).T;temporal=source['compute_dist_matrix_seqslam'](raw,seq_len=9,use_gpu=False)
    labels=source['generate_labels'](raw,temporal,[np.flatnonzero(p) for p in gt],9,topN=1)[0]
    features=np.stack([official_window_features(train[i-8:i+1],source) for i in range(8,len(train))])
    assert features.shape==(592,4) and np.isfinite(features).all()
    counts={int(k):int(v) for k,v in zip(*np.unique(labels,return_counts=True))}
    (path/'train_class_counts.json').write_text(json.dumps(counts,indent=2));print('Training classes',counts,flush=True)
    pipeline,_,_=source['mlp_train'](features,labels,str(path)+'/', 'smr')
    results=[];per=[];max_difference=0.;rank_equal=True
    for role in ['train','validation']:
        scores=np.load(data/f'{role}_cosplace_scores.npy');identity=ids[f'{role}_cosplace']
        assert digest(data/f'{role}_cosplace_scores.npy')==identity['scores_sha256']
        q=canonical_rows(rows,identity['query_ids']);g=canonical_rows(rows,identity['gallery_ids'])
        positives=index_positives(np.array([r['frame_index'] for r in q]),np.array([r['frame_index'] for r in g]),5)
        official=source['compute_dist_matrix_seqslam']((2-2*scores).T,seq_len=9,use_gpu=False)
        matcher=SmrMatcher(ROOT,pipeline);hits=[];accepted=[];a=np.argsort(-scores,axis=1,kind='stable')
        for i,s in enumerate(scores):
            ranking,meta=matcher.step(s);valid=ranking[:10]>=0
            hit=np.zeros(10,dtype=bool);hit[valid]=positives[i,ranking[:10][valid]];hits.append(hit);accepted.append(not meta['abstained'])
            if i>=8:
                total=np.zeros(len(s)-8,dtype=np.float32)
                for lag in range(9):total+=(2-2*scores[i-lag,8-lag:len(s)-lag]).astype(np.float32)
                max_difference=max(max_difference,float(np.max(np.abs(total-official[:,i-8]))))
                rank_equal=rank_equal and bool(np.array_equal(np.argsort(total,kind='stable')[:10],np.argsort(official[:,i-8],kind='stable')[:10]))
            per.append(dict(split=role,method='SMR_first_filter_adapted',query_image_id=identity['query_ids'][i],
                common_valid=i>=8,top1_image_id='' if ranking[0]<0 else identity['gallery_ids'][ranking[0]],
                correct_at_1=bool(hit[0]),correct_at_5=bool(hit[:5].any()),correct_at_10=bool(hit.any()),
                A_correct=bool(positives[i,a[i,0]]),abstained=meta['abstained'],metadata=json.dumps(meta)))
        hits=np.array(hits);accepted=np.array(accepted);mask=np.arange(len(scores))>=8;ac=positives[np.arange(len(scores)),a[:,0]]
        results.append(dict(split=role,method='SMR_first_filter_adapted',
            common={f'R@{k}':dict(correct=int(hits[mask,:k].any(1).sum()),queries=int(mask.sum()),recall=float(hits[mask,:k].any(1).mean())) for k in [1,5,10]},
            full_stream_with_startup={f'R@{k}':dict(correct=int(hits[:,:k].any(1).sum()),queries=len(scores),recall=float(hits[:,:k].any(1).mean())) for k in [1,5,10]},
            accepted_queries=int((accepted&mask).sum()),abstained_queries=int((~accepted&mask).sum()),
            rescue=int((mask&~ac&hits[:,0]).sum()),harm=int((mask&ac&~hits[:,0]).sum())))
    assert max_difference<2e-5 and rank_equal,(max_difference,rank_equal)
    (path/'metrics.json').write_text(json.dumps(dict(development_only=True,adaptation_not_official_benchmark=True,results=results,
        original_source_float32_convolution_max_difference=max_difference,original_source_top10_rank_equal=rank_equal,
        trained_pipeline_sha256=digest(path/'smr_pipeline.pkl'),internal_SMOTE_CV_not_independent=True),indent=2))
    with (path/'per_query.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
    print(json.dumps(results),flush=True)

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2]);return
    declaration=ROOT/'configs/v2/smr_adaptation_predeclaration.json';config=json.loads(declaration.read_text())
    run=Run(ROOT,'g3_smr_adaptation',config,dict(predeclaration_sha256=digest(declaration),official_commit='82c88c90377110ce7a3340872f3e1179c3f2d396'))
    print(run.id,flush=True);update_state(ROOT,latest_run_id=run.id)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),str(Path(__file__).resolve()),'--worker',str(run.path)],
        {'PYTHONPATH':'','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
    run.write('checks.json',dict(passed=True,exact_official_selected_function_bodies=True,all_abstentions_count_as_misses=True,
        own_adaptive_rule_unchanged=True,new_independent_performance_unopened=True))
    (run.path/'interpretation.md').write_text('SMR fixed-source first-filter adaptation; not the published benchmark protocol. Training uses Nordland train only, four ratios, original supervised four-class MLP/SMOTE. Original training CV follows oversampling and is not independent evidence. Val/test rejection stays in the Recall denominator. No official restoration, no dataset-specific external retraining. All differences are predeclared.\n')
    print(json.dumps({'run':run.id,'metrics':json.loads((run.path/'metrics.json').read_text())}),flush=True)

if __name__=='__main__':main()
