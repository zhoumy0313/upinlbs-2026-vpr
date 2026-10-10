"""Immutable freeze after metadata/galleries/code checks and before query performance."""
import json,sys,subprocess,shutil
from pathlib import Path
from datetime import datetime,timezone
import torch
import numpy,scipy,sklearn,imblearn,joblib,PIL,torchvision,platform
from runtime import Run,digest,update_state,utc_now
from method_suite import specifications
ROOT=Path(__file__).resolve().parents[2]

def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());assert not state['new_independent_test_has_been_opened']
    assert state['stages']['G3']=='scientifically_negative'
    preflight=ROOT/'outputs_v2'/state['g4_factory_preflight_run'];assert json.loads((preflight/'checks.json').read_text())['passed']
    geo=ROOT/'outputs_v2'/state['g4_geo_audit_run'];assert json.loads((geo/'checks.json').read_text())['passed']
    audit=ROOT/'outputs_v2'/state['g4_audit_run'];gallery=ROOT/'outputs_v2'/state['g4_gallery_run'];g3=ROOT/'outputs_v2'/state['g3_adaptive_run'];smr=ROOT/'outputs_v2'/state['g3_smr_run']
    for p in [audit,gallery,g3,smr]:assert json.loads((p/'checks.json').read_text())['passed']
    declaration=dict(protocol='one independent evaluation; empirical track A; no post-test tuning',radius_m=[25,10,50],
        common_startup_exclusion_per_traversal=8,GT='Euclidean UTM zone56J, distance <= radius, closed-set only; GPS offline only',
        no_positive_queries_reported=True,all_queries_still_advance_history=True,ordering='source pano_id traversal/frame ascending; reference gallery one traversal',
        velocity_is_index_step_not_meters=True,rounding='np.rint ties-even; whole path invalid if any index out of gallery',
        gallery_sampling='README nominal5m; actual audited median adjacent GPS steps gallery11.4176m/query11.9630m; source-frame gaps irregular. Documentation-vs-observation discrepancy disclosed, no resampling.',
        query_accuracy_batch_size=1,gallery_batch_size=16,image_size_hw=[224,224],seed=0,
        descriptor_tolerance=1e-5,score_tolerance=1e-5,rank_mismatches_disclosed_not_hidden=True,
        repetitions_for_latency=3,warmup_images=20,batch_size_for_latency=1,CUDA_sync=True,clocks_locked=False,
        software_versions=dict(python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,
            imblearn=imblearn.__version__,joblib=joblib.__version__,Pillow=PIL.__version__,torch=torch.__version__,torchvision=torchvision.__version__,CUDA=torch.version.cuda),
        latency_methods=['A-only','B-only','DINOv2-only','RRF_k60','AB_fixed_0.75','fixed_T_best','fixed_blend_best','adaptive_full','SMR_first_filter_adapted'],
        sensitivity_not_selection=True,contiguous_block_size=100,independent_test_opened=False)
    declaration['illustrative_examples_selection']='First chronological common query in fixed rescue/harm/bothwrong/adaptive-loses-fixed categories; unavailable cases explicit. Photos local only.'
    declaration['development_protocol']=dict(dataset='Nordland-Part-2020',train_ordinal=[1,600],validation_ordinal=[701,1000],gallery_ordinal=[1,1750],
        positive_absolute_ordinal_difference=5,old_seen_holdout=[1101,1750],old_seen_Gardens_Point='night_right; post_hoc only',
        independent_is_relative_to_our_method_tuning=True,upstream_encoder_pretraining_overlap_not_audited=True)
    scales=json.loads((g3/'train_gap_scales.json').read_text());interior=json.loads((g3/'metrics.json').read_text())['fixed_G2_interior_reference']['settings']
    declaration['methods']=specifications(interior,scales)
    run=Run(ROOT,'g4_freeze_audit',declaration,dict(audit=audit.name,gallery=gallery.name,SMR=smr.name));print(run.id,flush=True)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q','--junitxml='+str(run.path/'regression.xml')],
        {'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    for row in json.loads((audit/'manifest.json').read_text())['records']:
        assert digest(ROOT/row['relative_path'])==row['sha256'],row['image_id']
    # Checkpoint code and pre-test plans before writing the immutable freeze.
    run.command([str(ROOT/'.venv-p0/bin/python'),'experiments/temporal_vpr/archive_checkpoint.py','G4_pretest_code'])
    name='v2_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');folder=ROOT/'freezes'/name;folder.mkdir(parents=True,exist_ok=False)
    shutil.copy2(smr/'smr_pipeline.pkl',folder/'smr_pipeline.pkl')
    shutil.copy2(ROOT/'third_party/vpr-smr-predictor/LICENSE',folder/'SMR_LICENSE.txt')
    selected=list((ROOT/'experiments/temporal_vpr').rglob('*.py'))+list((ROOT/'configs/v2').glob('*.json'))+[
        ROOT/'configs/model_sources.json',ROOT/'src/vpr_research/encoders/frozen.py',ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json',audit/'manifest.json',audit/'metrics.json',
        gallery/'gallery_identities.json',preflight/'checks.json',preflight/'metrics.json',geo/'metrics.json',geo/'checks.json',g3/'train_gap_scales.json',g3/'metrics.json',smr/'metrics.json',smr/'smr_pipeline.pkl',folder/'smr_pipeline.pkl']
    for name in ['cosplace','eigenplaces','dinov2']:selected.append(gallery/(name+'_gallery.npy'))
    for value in json.loads((ROOT/'configs/model_sources.json').read_text()).values():
        if isinstance(value,dict):selected.append(ROOT/value['checkpoint'])
    hashes={p.relative_to(ROOT).as_posix():digest(p) for p in selected}
    for p in selected:
        if p.is_relative_to(ROOT/'experiments/temporal_vpr') or p.is_relative_to(ROOT/'configs'):
            copy=folder/'source_snapshot'/p.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes())
    for source in [audit/'manifest.json',audit/'metrics.json',gallery/'gallery_identities.json',g3/'train_gap_scales.json']:
        shutil.copy2(source,folder/('data_'+source.name if source.parent==audit else source.name))
    shutil.copy2(ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json',folder/'development_data_manifest.json')
    f=dict(**declaration,created_utc=utc_now(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        data_audit=audit.relative_to(ROOT).as_posix(),gallery_build=gallery.relative_to(ROOT).as_posix(),
        SMR_pipeline=(folder/'smr_pipeline.pkl').relative_to(ROOT).as_posix(),device='cuda' if torch.cuda.is_available() else 'cpu',file_sha256=hashes)
    with (folder/'freeze.json').open('x') as stream:json.dump(f,stream,indent=2,allow_nan=False)
    (folder/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.relative_to(folder).as_posix()+'\n' for p in sorted(folder.rglob('*')) if p.is_file()))
    (folder/'README.md').write_text('Immutable pre-test protocol. Do not modify. Full code/config snapshots and small trained SMR classifier with MIT source notice included. Dataset photos, external pretrained checkpoints and descriptor arrays stay local by exact SHA and source/download recipes. No independent retrieval performance was opened at creation.\n')
    run.write('metrics.json',dict(freeze=folder.name,freeze_sha256=digest(folder/'freeze.json'),code_commit=f['source_commit'],independent_performance_opened=False))
    run.write('checks.json',dict(passed=True,tests=56,metadata_gallery_identity_verified=True,source_commit_before_freeze=True))
    (run.path/'per_query.csv').write_text('independent_performance_opened\nfalse\n')
    (run.path/'interpretation.md').write_text('Immutable freeze created after code regression and gallery metadata identity, before independent performance. All comparison/sensitivity/latency choices fixed, including negative adaptive direction.\n')
    update_state(ROOT,freeze_directory=folder.relative_to(ROOT).as_posix(),latest_run_id=run.id)
    run.command(['git','add','freezes','docs/goals'])
    run.command(['git','-c','user.name=Codex','-c','user.email=codex@localhost','commit','-m','G4: immutable pre-test V2 freeze'])
    run.command(['git','push','origin','research/temporal-vpr-v2'])
    print(json.dumps(dict(freeze=folder.name,run=run.id,sha256=digest(folder/'freeze.json'))),flush=True)

if __name__=='__main__':main()
