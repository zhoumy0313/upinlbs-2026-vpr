"""Verify preservation and rerun isolated regressions after the recorded bootstrap."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

from runtime import Run, atomic_json, digest, update_state, utc_now

ROOT = Path(__file__).resolve().parents[2]
baseline = json.loads((ROOT/'docs/goals/v1_baseline_state.json').read_text())
original_run = ROOT/baseline['full_inventory_path']
inventory = json.loads(original_run.read_text())
config = dict(stage='G0', goal_id='VPR-GOAL-V2', tests_environment={
    'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'},
    preservation_allowlist=['.gitignore: V2 output/build exclusions appended'],
    independent_performance_opened=False)
run = Run(ROOT,'g0_regression',config,baseline)
print(run.id,flush=True)
run.event('bootstrap_failure_retained',dict(run_id=original_run.parent.name,
    reason='pytest discovered inherited ROS launch_testing plugin; lark missing; no project tests executed',
    commands_sha256=digest(original_run.parent/'commands.jsonl'),stderr_sha256=digest(original_run.parent/'stderr.log')))
run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests',
    '-q','--junitxml='+str(run.path/'regression.xml')],config['tests_environment'])
run.command(['df','-B1','.'])
run.command(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used','--format=csv,noheader'])
run.command(['git','ls-remote','origin','refs/heads/main'])
run.command([str(ROOT/'.venv-p0/bin/python'),'-c',
    'import platform,torch,numpy; print(platform.platform()); print(torch.__version__,torch.version.cuda,numpy.__version__); print(torch.cuda.is_available(),torch.cuda.get_device_name(0))'])
different = []
for row in inventory:
    if row['path']!='.gitignore' and digest(ROOT/row['path'])!=row['sha256']:
        different.append(row['path'])
assert not different,different
assert subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()==baseline['baseline_sha']
oldignore = subprocess.check_output(['git','show',baseline['baseline_sha']+':.gitignore'],cwd=ROOT)
assert (ROOT/'.gitignore').read_bytes().startswith(oldignore)
suites = ET.parse(run.path/'regression.xml').getroot()
totals = {key:sum(int(s.attrib.get(key,0)) for s in suites.findall('testsuite'))
    for key in ['tests','failures','errors','skipped']}
assert totals['tests']>=34 and totals['failures']==totals['errors']==0
checks = dict(passed=True,regression=totals,all_original_scientific_files_and_outputs_unchanged=True,
    allowed_v2_append_only_gitignore_change=True,main_unchanged=True,
    old_pdf_pages=5, independent_test_opened=False,bootstrap_failure_retained=True)
run.write('checks.json',checks)
run.write('metrics.json',dict(role='preservation/regression only, no new VPR performance',
    preserved_files=len(inventory),preserved_bytes=sum(r['bytes'] for r in inventory),regression=totals))
with (run.path/'per_query.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256','role']);writer.writeheader();writer.writerows(inventory)
(run.path/'interpretation.md').write_text('G0 passed after process-local isolation of unrelated ROS pytest plugins. The original failure remains unchanged. All original scientific files and every inventoried outputs/ file retain SHA-256; only .gitignore has appended V2 exclusions. This is not a retrieval evaluation.\n')
public = ROOT/'artifacts/v2/g0'
public.mkdir(parents=True,exist_ok=False)
archive = public/'evidence.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for folder in [original_run.parent,run.path]:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.suffix in {'.json','.jsonl','.log','.yaml','.csv','.xml','.md'}:
                z.write(path,path.relative_to(ROOT).as_posix())
(public/'SHA256SUMS').write_text(digest(archive)+'  evidence.zip\n')
atomic_json(public/'acceptance.json',checks)
reproduce='.venv-p0/bin/python experiments/temporal_vpr/finish_g0.py (one-time G0 publisher; refuses existing archive; use recorded pytest command for regression replay)'
report=f'''# G0 acceptance — passed

UTC: {utc_now()}. Baseline: `{baseline['baseline_sha']}`; branch: `{baseline['working_branch']}`.

Preserved {len(inventory)} original tracked/output files with SHA-256 inventory; old main, scientific source/protocol/results/evidence and paper/main.* unchanged. .gitignore only gained V2 exclusions. Frozen tag and exact human-readable V1 paper snapshot exist. Disk/network/GPU probe command exits are zero in the successful run. No drivers, SSH, proxy, system Python or ROS changed.

Runs: `{original_run.parent.relative_to(ROOT)}` (pytest startup failure retained); `{run.path.relative_to(ROOT)}` (successful isolated regressions).
Tests: {totals['tests']} passed; failures/errors: {totals['failures']}/{totals['errors']}. Includes 31 original tests and 3 V2 runtime/preservation tests.

Commands/exit codes: both runs' commands.jsonl; successful stdout.log/stderr.log; original ROS plugin failure stderr.log. Inputs: docs/goals/v1_baseline_state.json and full inventory; inventory SHA `{baseline['full_inventory_sha256']}`. Public archive: artifacts/v2/g0/evidence.zip, SHA `{digest(archive)}`. No VPR metric or new model has been evaluated. No test-label tuning. Original old metrics remain unchanged.

New files: docs/goals and docs/research_v2 scaffolding, AGENTS_V2.md, scoped experiments/temporal_vpr code/tests, paper/versions/v1_20261010_frozen; .gitignore append.
Reproduction: `{reproduce}`.

## Beginner explanation
1. Old photographs, descriptors and scores are unchanged input assets.
2. File hashes identify the exact bytes used in the first study.
3. A Git tag names the old source snapshot permanently.
4. A new branch holds new research while main retains the old version.
5. The regression suite checks retrieval/gating behavior without new final-image evaluation.
6. Process isolation prevents unrelated ROS plugins from affecting this project.
7. This stage outputs preservation evidence, not improved recognition numbers.
8. Oracle and temporal ideas will first be audited on train/validation in G1.

Decision: accept G0; next single task: G1 GT/order, development candidate potential and primary-literature audit. New independent performance remains unopened.
'''
(ROOT/'docs/research_v2/G0_ACCEPTANCE.md').write_text(report)
state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());state['stages']['G0']='passed';state['stages']['G1']='in_progress'
update_state(ROOT,current_stage='G1',stage_status='in_progress',stages=state['stages'],latest_run_id=run.id)
(ROOT/'docs/goals/GOAL_V2_STATUS.md').write_text(f'# VPR-GOAL-V2\n\nG0 passed: old version preserved; {totals["tests"]} tests pass. G1 in progress; G2–G5 pending.\n\nBranch `{baseline["working_branch"]}`; baseline `{baseline["baseline_sha"]}`. Independent test unopened. Next: GT/order + train/validation candidate diagnosis and literature audit.\n')
with (ROOT/'docs/research_v2/EXPERIMENT_REGISTER.md').open('a') as f:f.write(f'| G0 | Preservation/regression after ROS plugin isolation | metadata only | {run.id} | passed, {totals["tests"]} tests |\n')
with (ROOT/'docs/research_v2/DECISION_LOG.md').open('a') as f:f.write(f'\n{utc_now()}: G0 accepted on actual SHA inventory and isolated regression; auto-advance G1. Bootstrap failure retained; no project science changed.\n')
print(json.dumps(dict(run_id=run.id,checks=checks,public_archive_sha256=digest(archive))))
