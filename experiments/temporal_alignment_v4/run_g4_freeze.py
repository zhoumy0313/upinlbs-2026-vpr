import json
from runtime import *
from run_g3 import choose
def main():
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());assert not s['independent_retrieval_opened'] and s['stages']['g3']=='passed'
    grid=json.loads((ROOT/'configs/v4/search_grid.yaml').read_text());selected=json.loads((ROOT/'configs/v4/selected_methods.json').read_text());baseline=json.loads((ROOT/'docs/research_v4/BASELINE_RESULTS.json').read_text())['results']
    timing_names=['A','B','RRF60','L3','L5','L9','old_fixed_L9',selected['strongest_selected']['name'],selected['proposed']['name']]
    for kind in ['AB','index_global','index_R1','index_R2','time','time_global','time_R1','time_R2']:
        timing_names.append(choose([x for x in grid['baselines'] if x['kind']==kind],baseline)['name'])
    for specs in selected['same_pool_controls'].values():timing_names.extend(x['name'] for x in specs)
    timing_names=list(dict.fromkeys(timing_names))
    specs=grid['baselines']+[selected['proposed']];timing=[x for n in timing_names for x in specs if x['name']==n];assert len(timing)==len(timing_names)
    write(ROOT/'configs/v4/frozen_evaluation.yaml',dict(all_test_methods=specs,timing_methods=timing,test_hz=5,all_radii=[.25,.5,1.],seed=0,rejection_policy='none',timing=dict(batch_size=1,warmup=20,passes=3,decode=True,CPU_transfer=True,full_gallery_cosine=True,history=True,alignment=True,refinement=True,full_ranking=True,cuda_synchronization=True),timing_selection='all mandatory families plus developer-selected strongest and matched-pool controls; no test-derived method selection',selection_sha256=sha(ROOT/'configs/v4/selected_methods.json'),protocol_sha256=sha(ROOT/'configs/v4/protocol_accepted.yaml'),development_feature_run=s['development_feature_run'],primary_accuracy_encoding_batch=16,online_timing_encoding_batch=1,online_accuracy_audit='report all cached/batch-one differences, no claim of equality unless measured'))
    run=Run('g4_freeze',dict(independent_not_opened=True,test_sequence='freiburg3_long_office_household',methods=len(specs),timing_methods=len(timing)))
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','experiments/endpoint_vpr/tests','experiments/paper_v2/test_manuscript_audit.py','experiments/temporal_alignment_v4/tests','-q','--junitxml='+str(run.path/'all_regression.xml')],dict(PYTHONPATH='',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'))
    run.checkpoint('G4 code and evaluation pre-freeze checkpoint')
    folder=ROOT/'freezes'/('v4_'+__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%SZ'));folder.mkdir(exist_ok=False)
    paths=[p for p in (ROOT/'experiments/temporal_alignment_v4').rglob('*.py') if '__pycache__' not in p.parts]+list((ROOT/'configs/v4').glob('*'))+list((ROOT/'data/manifests/v4').glob('*.json'))+[ROOT/'configs/model_sources.json',ROOT/'src/vpr_research/encoders/frozen.py',ROOT/'experiments/endpoint_vpr/core.py',ROOT/'outputs_v4'/s['development_feature_run']/'model_identity.json']
    freeze=dict(freeze_id=folder.name,created_utc=utc(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),test_retrieval_not_opened=True,file_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},raw_archives={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'data/raw/v4/tum_rgbd/archives').glob('*.tgz'))},protocol=json.loads((ROOT/'configs/v4/protocol_accepted.yaml').read_text()),evaluation=json.loads((ROOT/'configs/v4/frozen_evaluation.yaml').read_text()),model_identity=json.loads((ROOT/'outputs_v4'/s['development_feature_run']/'model_identity.json').read_text()),roles=dict(development='freiburg2_pioneer_slam',test='freiburg3_long_office_household'),no_GT_online=True)
    write(folder/'freeze.json',freeze);write(folder/'SHA256SUMS.json',dict(freeze_json_sha256=sha(folder/'freeze.json')))
    s=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text());s['freeze_folder']=str(folder.relative_to(ROOT));s['g4_freeze_run']=run.id;write(ROOT/'docs/goals/GOAL_V4_STATE.json',s)
    run.finish(dict(freeze_folder=str(folder.relative_to(ROOT)),freeze_sha256=sha(folder/'freeze.json'),test_methods=len(specs),timing_methods=len(timing)),passed=False)
    # A second independent checkpoint run records freeze publication, preserving first receipt.
    cp=Run('freeze_publication',dict(freeze_sha256=sha(folder/'freeze.json')));cp.finish(dict(freeze_folder=str(folder.relative_to(ROOT))),passed=True);cp.checkpoint('G4 immutable freeze before first independent retrieval')
    print(json.dumps(dict(freeze=str(folder.relative_to(ROOT)),timing_methods=len(timing))),flush=True)
if __name__=='__main__':main()
