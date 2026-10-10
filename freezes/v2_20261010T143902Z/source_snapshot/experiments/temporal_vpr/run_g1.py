"""G1 development-only diagnosis; original model source/cache hashes are enforced."""
import csv
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from vpr_research.artifacts import load_descriptors
from vpr_research.core import cosine_scores,index_positives
from runtime import Run,digest,atomic_json,update_state
from diagnostics import canonical_rows,rank_diagnostics,union_oracle,duplicate_audit,sequence_rescue_diagnostic

manifest=ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json'
gardens_manifest=ROOT/'data/manifests/p1_20261010_132030_gardens_point_manifest_v2.json'
config=dict(stage='G1',splits=['train','validation'],ks=[1,5,10,20,50],positive_radius_frames=5,
    used_old_test_for_method_selection=False,sequence_support_diagnostic_horizon=3,
    diagnostic_support_candidate_k=50,final_test_retrieval_computed=False,
    descriptor_source_policy='strict V1 identity guard; stale DINOv2 identity rebuilt in new run')
run=Run(ROOT,'g1_diagnosis',config,dict(manifest=str(manifest.relative_to(ROOT)),sha256=digest(manifest),
    gardens_manifest_sha256=digest(gardens_manifest),role='train/validation performance; old labels/images descriptive audit only'))
print(run.id,flush=True)
update_state(ROOT,latest_run_id=run.id)
run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q',
    '--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
run.command([str(ROOT/'.venv-p0/bin/python'),'scripts/extract_dev_descriptors.py',
    '--manifest',str(manifest),'--method','dinov2','--run-dir',str(run.path)],{'PYTHONPATH':''})
records=json.loads(manifest.read_text())['records']
gardens=json.loads(gardens_manifest.read_text())['records']
for r in records+gardens:
    path=ROOT/r['relative_path']
    assert digest(path)==r['sha256'],r['image_id']
    with Image.open(path) as im:
        im.load();assert im.size==(r['width'],r['height'])
for traverse in ['summer','winter']:
    rows=[r for r in records if r['traverse']==traverse]
    assert [r['frame_index'] for r in rows]==list(range(1,1751))
    assert [r['file_numeric_id'] for r in rows]==list(range(251,2001))
duplicates={role:duplicate_audit([r for r in records if r['traverse']=='winter' and
    (role=='all' or r['split']==role)]) for role in ['all','train','validation','test']}
trainhash={r['sha256'] for r in records if r['split']=='train'}
valhash={r['sha256'] for r in records if r['split']=='validation'}
assert not trainhash&valhash
audit=dict(nordland_raw_ids=[251,2000],ordinal_ids=[1,1750],decode_verified_images=len(records)+len(gardens),
    summer_winter_filename_alignment='exact numeric ID pair; not metric pose/verified full spatial alignment',
    winter_duplicates=duplicates,train_validation_shared_exact_bytes=0,
    gardens_strict_correspondence='VPR_Tutorial GThard identity 200; GTsoft-only entries ignored, not positives',
    gardens_gt_loader_sha256=digest(ROOT/'third_party/VPR_Tutorial/datasets/load_dataset.py'),
    gardens_gt_metrics_sha256=digest(ROOT/'third_party/VPR_Tutorial/evaluation/metrics.py'),
    gt_limitations=['Nordland +/-5 frames is not meters','Visual/filename alignment cannot establish precise pose',
      'Dense duplicate station frames and train-to-test changes are not a proven domain-shift explanation'],
    independent_performance_opened=False)
run.write('data_audit.json',audit)
cache_dirs={m:ROOT/'outputs/p3_eigenplaces_20261010_141736_ayAvV5'/m for m in ['cosplace','eigenplaces']}
cache_dirs['dinov2']=run.path/'dinov2'
summary=dict(protocol=config,data_roles='development only',splits={},cache_fingerprints={})
rows_out=[]; examples=[]
for role in ['train','validation']:
    result={}; ranks_by_model={}
    for model,cache in cache_dirs.items():
        gallery,dbids,fp=load_descriptors(cache,manifest,'gallery')
        query,qids,_=load_descriptors(cache,manifest,role)
        dbrows=canonical_rows(records,dbids); qrows=canonical_rows(records,qids)
        df=np.array([r['frame_index'] for r in dbrows]);qf=np.array([r['frame_index'] for r in qrows])
        assert all(r['split']==role for r in qrows)
        positive=index_positives(qf,df,config['positive_radius_frames'])
        scores=cosine_scores(query,gallery)
        ranks,earliest,metrics=rank_diagnostics(scores,positive)
        ranks_by_model[model]=ranks
        support=sequence_rescue_diagnostic(earliest)
        duplicated_ids={i for g in duplicates[role]['groups'] for i in g}
        result[model]=dict(recall=metrics,retrieval_missing_at_50=int((earliest>50).sum()),
            rank_error_at_50=int(((earliest>1)&(earliest<=50)).sum()),
            duplicate_ambiguous_gt_records=len(duplicated_ids),
            sequence_rescue_possible_diagnostic_only=int(support.sum()),
            earliest_positive_rank_median=float(np.median(earliest)),
            source_fingerprint_sha256=digest(cache/'fingerprint.json'))
        summary['cache_fingerprints'][model]=dict(path=str(cache.relative_to(ROOT)),sha256=digest(cache/'fingerprint.json'),
            identity_guard_passed=True,model=fp['model'])
        for i,row in enumerate(qrows):
            rows_out.append(dict(split=role,model=model,query_image_id=row['image_id'],
                ordinal_frame=row['frame_index'],first_positive_rank=int(earliest[i]),
                top1_image_id=dbids[ranks[i,0]],correct_at_1=bool(earliest[i]==1),
                retrieval_missing_at_50=bool(earliest[i]>50),rank_error_at_50=bool(1<earliest[i]<=50),
                ambiguous_gt_exact_duplicate=row['image_id'] in duplicated_ids,
                sequence_rescue_possible_diagnostic_only=bool(support[i]),
                top50_image_ids=json.dumps([dbids[j] for j in ranks[i,:50]])))
        if model=='cosplace':
            for kind,mask in [('rank_error',(earliest>1)&(earliest<=50)),('retrieval_missing',earliest>50)]:
                for i in np.flatnonzero(mask)[:2]:
                    bestpos=int(ranks[i,earliest[i]-1]);top=int(ranks[i,0])
                    chosen=[qrows[i],dbrows[top],dbrows[bestpos]]
                    panel=Image.new('RGB',(960,205),'white');draw=ImageDraw.Draw(panel)
                    for n,(label,r) in enumerate(zip(['winter query','predicted top1','best GT-positive (offline only)'],chosen)):
                        with Image.open(ROOT/r['relative_path']) as im:panel.paste(im.convert('RGB').resize((320,180)),(n*320,25))
                        draw.text((n*320+3,2),label,fill='black')
                    name=f'{role}_{kind}_{i}.png';panel.save(run.path/'figures'/name)
                    examples.append(dict(split=role,error_type=kind,query_image_id=qrows[i]['image_id'],
                        predicted_image_id=dbrows[top]['image_id'],best_positive_image_id=dbrows[bestpos]['image_id'],
                        positive_rank=int(earliest[i]),figure=str((run.path/'figures'/name).relative_to(ROOT)),
                        role='offline visual GT/aliasing diagnostic, not new spatial ground truth'))
    result['A_B_candidate_union_oracle']=union_oracle(ranks_by_model['cosplace'],ranks_by_model['eigenplaces'],positive)
    summary['splits'][role]=result
run.write('metrics.json',summary)
run.write('examples.json',examples)
with (run.path/'per_query.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows_out[0]));writer.writeheader();writer.writerows(rows_out)
run.write('checks.json',dict(strict_cache_identity_verified=True,all_images_verified_and_decoded=True,
    train_val_disjoint_hashes=True,old_test_used_for_selection=False,new_independent_performance_opened=False,
    ordinal_vs_filename_checked=True,raw_logs_preserved=True,per_query_rows=len(rows_out)))
(run.path/'interpretation.md').write_text('Train/validation label-aware diagnosis only. Sequence support is an offline GT-based upper-bound diagnostic and is never an online input. Exact duplicate ambiguity overlaps the ranking categories. Filename/visual inspection cannot prove metric GT. Stale DINOv2 descriptors were rebuilt using current unchanged V1 extractor; original stale caches preserved.\n')
print(json.dumps(dict(run_id=run.id,summary={role:{m:{k:v['recall'] for k,v in
    summary['splits'][role][m]['recall'].items()} for m in cache_dirs} for role in ['train','validation']},
    duplicates={role:{k:v for k,v in d.items() if k!='groups'} for role,d in duplicates.items()})),flush=True)
