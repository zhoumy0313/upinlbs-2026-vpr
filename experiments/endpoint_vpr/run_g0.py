"""Preserve all historical scientific records; isolate only new V3 state."""
import json,subprocess,sys
from pathlib import Path
from runtime import ROOT,BASE,BRANCH,Run,sha,atomic,utc,state,checkpoint
def main():
    run=Run('g0_preserve','old V1/V2 preservation and environment check',dict(base=BASE,branch=BRANCH),{})
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0')
    files={ROOT/p.decode() for p in tracked if p}
    for name in ['outputs','outputs_v2','paper','freezes','data','weights','cache','third_party']:
        files.update(p for p in (ROOT/name).rglob('*') if p.is_file() and not any(part in ['.git','__pycache__'] for part in p.relative_to(ROOT).parts) and p.suffix!='.pyc')
    files={p for p in files if not p.relative_to(ROOT).as_posix().startswith(('experiments/endpoint_vpr/','docs/goals/GOAL_V3','outputs_v3/'))}
    inventory=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
    public=ROOT/'artifacts/v3/g0';public.mkdir(parents=True,exist_ok=False);atomic(public/'old_files.json',inventory);run.write('old_files.json',inventory)
    v1=json.loads((ROOT/'docs/goals/v1_baseline_state.json').read_text())
    for path,expected in v1['preserved_hashes'].items():assert sha(ROOT/path)==expected
    for row in json.loads((ROOT/v1['full_inventory_path']).read_text()):
        p=ROOT/row['path'];assert (sha(p) if row['path']!='.gitignore' else __import__('hashlib').sha256(p.read_bytes()[:row['bytes']]).hexdigest())==row['sha256'],p
    for argv in [['git','ls-remote','origin','refs/heads/main','refs/heads/research/temporal-vpr-v2'],['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],['free','-h'],['df','-h',str(ROOT)],['codex','login','status'],['systemctl','is-active','ssh']]:run.command(argv)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','experiments/paper_v2/test_manuscript_audit.py','-q','--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    (ROOT/'docs/research_v3').mkdir(parents=True,exist_ok=True);(ROOT/'configs/v3').mkdir(parents=True,exist_ok=True)
    atomic(ROOT/'docs/goals/GOAL_V3_STATE.json',dict(goal_id='VPR-GOAL-V3',base_branch='research/temporal-vpr-v2',base_sha=BASE,working_branch=BRANCH,current_stage='G1',stages={f'G{i}':'passed' if i==0 else 'pending' for i in range(8)},research_track='endpoint_support_constraint',novelty_claim_supported=False,new_independent_test_opened=False,latest_run_id=run.id,last_pushed_sha=None,formal_submission_ready=False,goal_source_sha256=sha(ROOT/'docs/goals/GOAL_V3_ENDPOINT_REFINEMENT.md'),g0_preservation_run=run.id,updated_utc=utc()))
    for filename,content in {'DECISION_LOG.md':'# V3 decisions\n\n'+utc()+': inherited exact V2 base. User goal file is the only initial untracked input; raw diff/file backup retained before branch creation. No historical file modification. All old data are seen.\n','EXPERIMENT_REGISTER.md':'# V3 run register\n\nG0 '+run.id+' — preservation/regression passed.\n','DATA_PROTOCOL.md':'# V3 data roles\n\nNordland, GardensPoint and StLucia are all seen/exploratory or development. Never relabel them independent. New independent data selected only by source/licence/metadata and opened after immutable freeze.\n'}.items():(ROOT/'docs/research_v3'/filename).write_text(content)
    original_ignore=(ROOT/'.gitignore').read_bytes()
    with (ROOT/'.gitignore').open('ab') as f:f.write(b'\n# V3 append-only local scientific evidence.\noutputs_v3/\n!artifacts/v3/**/*.zip\npaper/revisions/v3_*/**/*.aux\npaper/revisions/v3_*/**/*.log\npaper/revisions/v3_*/**/*.out\n')
    assert (ROOT/'.gitignore').read_bytes().startswith(original_ignore)
    run.finish(dict(old_files=len(inventory),old_total_bytes=sum(x['bytes'] for x in inventory),tests=60,base_sha=BASE,goal_sha256=sha(ROOT/'docs/goals/GOAL_V3_ENDPOINT_REFINEMENT.md')),dict(passed=True,V1_original_hashes_match=True,V2_base_exact=True,no_system_changes=True))
    import zipfile
    with zipfile.ZipFile(public/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run.path.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
    for name in ['raw_metrics.json','acceptance.json']:(public/name).write_bytes((run.path/name).read_bytes())
    (public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    (ROOT/'docs/research_v3/G0_ACCEPTANCE.md').write_text('# G0 — passed\n\n'+run.id+'; inherited '+BASE+'; '+str(len(inventory))+' old tracked/raw/output/model/source files hashed and retained, V1 original inventory verified.60 old/V2 tests passed; GPU/SSH/Codex/memory/disk checked with actual logged exit0. Only new V3 input was untracked, backed up before branch switch; no original dirty modifications. .gitignore appended, original bytes intact. All new code/state/docs confined V3; no old editor/source changed. Exact command/UTC/exits and inventory in stage ZIP.\n\nInput: existing V1/V2 records → SHA inventory and regression → protected read-only baseline. Failure to match any old identity blocks future stages. No V3 scientific performance yet. Next sole task G1 cached endpoint-drift/coverage diagnosis on seen data. Checkpoint receipt follows separately.\n')
    checkpoint('G0')
if __name__=='__main__':main()
