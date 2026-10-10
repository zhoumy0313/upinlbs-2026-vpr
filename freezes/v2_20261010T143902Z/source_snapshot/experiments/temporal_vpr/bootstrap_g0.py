import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import uuid

ROOT = Path(sys.argv[1]).resolve()
def now():
    return datetime.now(timezone.utc).isoformat()
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    value = json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    tmp.write_text(value)
    json.loads(tmp.read_text())
    os.replace(tmp, path)
RUN_ID = 'g0_preserve_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
RUN = ROOT / 'outputs_v2' / RUN_ID
RUN.mkdir(parents=True, exist_ok=False)
(RUN / 'figures').mkdir()
commands = []
def command(argv):
    start = now()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    row = dict(argv=argv, cwd=str(ROOT), environment_overrides={}, started_utc=start,
               ended_utc=now(), exit_code=result.returncode)
    commands.append(row)
    with (RUN / 'commands.jsonl').open('a') as f:
        f.write(json.dumps(row) + '\n')
    with (RUN / 'stdout.log').open('a') as f:
        f.write('\nCOMMAND ' + json.dumps(argv) + '\n' + result.stdout)
    with (RUN / 'stderr.log').open('a') as f:
        f.write('\nCOMMAND ' + json.dumps(argv) + '\n' + result.stderr)
    if result.returncode:
        raise RuntimeError(f'Command exited {result.returncode}: {argv}; see {RUN}')
    return result.stdout.strip()

status = command(['git', 'status', '--porcelain=v1'])
head = command(['git', 'rev-parse', 'HEAD'])
branch = command(['git', 'branch', '--show-current'])
remote = command(['git', 'remote', '-v'])
if branch != 'main' or status != '?? docs/GOAL_V2_TEMPORAL_VPR.md':
    raise RuntimeError('Unexpected initial working tree; retain run and inspect before proceeding')
goal_original = ROOT / 'docs/GOAL_V2_TEMPORAL_VPR.md'
goal_sha = sha(goal_original)
tag = 'vpr-v1-frozen-20261010'
tags = command(['git', 'tag', '--list', tag])
if not tags:
    command(['git', 'tag', tag, head])
else:
    if command(['git', 'rev-list', '-n', '1', tag]) != head:
        raise RuntimeError('Existing frozen tag differs; never move it')
newbranch = 'research/temporal-vpr-v2'
if command(['git', 'branch', '--list', newbranch]):
    newbranch += '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
command(['git', 'switch', '-c', newbranch])

for rel in ['docs/goals', 'docs/research_v2', 'experiments/temporal_vpr', 'artifacts/v2',
            'paper/versions/v1_20261010_frozen']:
    (ROOT / rel).mkdir(parents=True, exist_ok=True)
(ROOT / 'docs/goals/GOAL_V2_TEMPORAL_VPR.md').write_bytes(goal_original.read_bytes())
snap = ROOT / 'paper/versions/v1_20261010_frozen'
paper_hashes = {}
for filename in ['main.tex', 'main.pdf', 'references.bib']:
    original = ROOT / 'paper' / filename
    target = snap / filename
    if target.exists():
        raise RuntimeError('Snapshot exists; do not overwrite')
    shutil.copy2(original, target)
    assert sha(original) == sha(target)
    paper_hashes['paper/' + filename] = sha(original)
dump(snap / 'source_manifest.json', dict(baseline_sha=head, files=paper_hashes,
     created_utc=now(), source_role='immutable V1 snapshot', pdf_pages=5))

tracked = command(['git', 'ls-files', '-z']).split('\0')
inventory = []
for rel in tracked:
    if rel and (ROOT / rel).is_file():
        inventory.append(dict(path=rel, bytes=(ROOT / rel).stat().st_size, sha256=sha(ROOT / rel), role='v1_tracked'))
for path in sorted((ROOT / 'outputs').rglob('*')):
    if path.is_file():
        inventory.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                              sha256=sha(path), role='v1_local_output'))
dump(RUN / 'v1_full_file_inventory.json', inventory)
with (RUN / 'per_query.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['path', 'bytes', 'sha256', 'role'])
    writer.writeheader()
    writer.writerows(inventory)
baseline = dict(goal_id='VPR-GOAL-V2', recorded_utc=now(), baseline_branch=branch,
    baseline_sha=head, working_branch=newbranch, initial_git_status=status, remote=remote,
    original_goal_file=str(goal_original.relative_to(ROOT)), original_goal_sha256=goal_sha,
    preserved_hashes={**paper_hashes, 'configs/protocol.yaml':sha(ROOT/'configs/protocol.yaml'),
      'artifacts/evidence/execution_evidence_20261010.zip':sha(ROOT/'artifacts/evidence/execution_evidence_20261010.zip')},
    full_inventory_path=str((RUN/'v1_full_file_inventory.json').relative_to(ROOT)),
    full_inventory_sha256=sha(RUN/'v1_full_file_inventory.json'),
    old_conclusions=dict(nordland_queries=650, nordland_cosplace_correct=92,
       nordland_eigenplaces_correct=65, nordland_gate25_correct=67,
       gardens_queries=200,gardens_cosplace_correct=69,gardens_eigenplaces_correct=72,
       gardens_gate25_correct=69),
    old_conclusions_source='docs/P4_FINAL_EXPERIMENT_REPORT.md',
    history_tag=tag, main_must_remain=head)
dump(ROOT/'docs/goals/v1_baseline_state.json', baseline)
state = dict(goal_id='VPR-GOAL-V2', baseline_sha=head, working_branch=newbranch,
    current_stage='G0', stage_status='in_progress',
    stages={s: 'in_progress' if s=='G0' else 'pending' for s in ['G0','G1','G2','G3','G4','G5']},
    latest_run_id=RUN_ID, selected_research_track=None,
    new_independent_test_has_been_opened=False, paper_revision='v1_preserved',human_action_required=[],
    updated_utc=now())
dump(ROOT/'docs/goals/GOAL_V2_STATE.json', state)
(ROOT/'docs/goals/GOAL_V2_STATUS.md').write_text('# VPR-GOAL-V2\n\nG0 保全进行中；G1–G5 尚未完成。\n\n旧 main: `'+head+'`。新分支: `'+newbranch+'`。\n独立测试尚未打开；不以旧测试选择新方法。\n')
ignore = ROOT/'.gitignore'
with ignore.open('a') as f:
    f.write('\n# V2 append-only local experiments; small public evidence has a separate directory.\noutputs_v2/\n!artifacts/v2/**/*.zip\npaper/revisions/**/*.aux\npaper/revisions/**/*.log\npaper/revisions/**/*.out\npaper/revisions/**/*.fls\npaper/revisions/**/*.fdb_latexmk\npaper/revisions/**/*.synctex.gz\n')
(ROOT/'experiments/temporal_vpr/AGENTS.md').write_text('# V2 authorized scope\n\nThe explicitly invoked `docs/goals/GOAL_V2_TEMPORAL_VPR.md` authorizes G0–G5 in new V2 paths. Temporal matching and fusion are allowed here; the original V1 five-feature gate and replacement-only protocol remain immutable. No changes to V1 source, protocol, outputs, artifacts, or paper/main.*. No final-test tuning; Nordland train/validation only for model choices. All runs append-only, all new Python requires unit/integration verification. Existing environment/SSH/proxy/drivers remain intact.\n')
(ROOT/'AGENTS_V2.md').write_text('# VPR-GOAL-V2 execution scope\n\nThe user explicitly invokes the canonical Goal. Its V2-only temporal/fusion scope supersedes V1 method restrictions for new files, not for the historical V1 protocol. Follow the full Goal, preserve all original tracked science files and local outputs, and do not rewrite main. New code: experiments/temporal_vpr; runs: outputs_v2; public evidence: artifacts/v2; papers: paper/revisions. New independent performance may only be opened after immutable freeze.\n')
for name, text in {
 'EXPERIMENT_REGISTER.md':'# Experiment register\n\n| Stage | Hypothesis/task | Data role | Run | Status |\n|---|---|---|---|---|\n| G0 | Preserve V1 and verify environment/tests | no new retrieval experiment | '+RUN_ID+' | in progress |\n',
 'DECISION_LOG.md':'# Decisions before new independent performance\n\n'+now()+': V2 scope registered. Preserve V1; use train/validation only for choices. No method selected.\n',
 'EVIDENCE_INDEX.md':'# Evidence index\n\nG0 original file inventory: `'+str((RUN/'v1_full_file_inventory.json').relative_to(ROOT))+'`; SHA-256 `'+sha(RUN/'v1_full_file_inventory.json')+'`.\n',
 'DATA_PROTOCOL.md':'# V2 data roles\n\nNordland ordinal 1–600 train, 701–1000 validation; buffers excluded. Old 1101–1750 holdout and Gardens Point have already been seen: descriptive/post-hoc only. No new independent performance opened. GT/order audit is next; no new thresholds selected.\n',
 'RELATED_WORK_MATRIX.md':'# Related work audit\n\nPending G1: read and verify SeqSLAM, Delta Descriptors, SMR, To Match, SU, RRF and UPINLBS 2025 ResNet-Sinkhorn. No novelty claim established.\n',
 'RESEARCH_SUMMARY.md':'# Current research status\n\nG0 in progress. V1 is a completed empirical negative-result draft; V2 is not a verified method or a submission candidate.\n',
 'HANDOFF_FOR_AUTHOR.md':'# Author handoff\n\nMingyang Zhou, University of Chinese Academy of Science, is the only confirmed author. Others/corresponding author pending human decision. No submission or authorship action authorized. V2 requires new independent evaluation and novelty review.\n',
}.items():
    (ROOT/'docs/research_v2'/name).write_text(text)
shutil.copy2(__file__, ROOT/'experiments/temporal_vpr/bootstrap_g0.py')
dump(RUN/'run_manifest.json',dict(run_id=RUN_ID,task='G0 preserve V1',started_utc=commands[0]['started_utc'],
    git_sha=head,working_branch=newbranch, config_sha256=goal_sha,metadata_only=True))
dump(RUN/'argv.json',dict(bootstrap_argv=sys.argv,cwd=str(ROOT),environment_overrides={}, commands=commands))
(RUN/'config_effective.yaml').write_text('goal_id: VPR-GOAL-V2\nstage: G0\nmode: preservation_and_regression_only\nold_protocol_readonly: true\n')
dump(RUN/'inputs.json',baseline)
command(['df','-B1','.'])
command(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used','--format=csv,noheader'])
command([str(ROOT/'.venv-p0/bin/python'),'-c',"import sys,torch; print(sys.version); print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_properties(0).total_memory)"])
command(['git','ls-remote','origin','refs/heads/main'])
command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','-q','--junitxml='+str(RUN/'v1_regression.xml')])
assert command(['git','rev-parse','main']) == head
for row in inventory:
    assert sha(ROOT/row['path']) == row['sha256'], row['path']
dump(RUN/'checks.json',dict(all_original_inventory_hashes_match=True, original_files=len(inventory),
      original_tests_exit_code=commands[-2]['exit_code'],main_unchanged=True,
      goal_verbatim=sha(ROOT/'docs/goals/GOAL_V2_TEMPORAL_VPR.md')==goal_sha,
      independent_test_opened=False,commands_exit_codes=[r['exit_code'] for r in commands]))
dump(RUN/'metrics.json',dict(experiment_role='G0 metadata/regression, not VPR performance',
     preserved_files=len(inventory),preserved_total_bytes=sum(r['bytes'] for r in inventory),
     v1_retrieval_metrics_recomputed=False))
(RUN/'interpretation.md').write_text('G0 records metadata and regression tests only. This run performs no new retrieval experiment, tunes no method, and opens no independent performance. Old files are SHA-256 verified after the regression tests. Next: G1 GT/order and development-only candidate/literature audit.\n')
dump(RUN/'argv.json',dict(bootstrap_argv=sys.argv,cwd=str(ROOT),environment_overrides={},commands=commands))
print(json.dumps(dict(run_id=RUN_ID,run_path=str(RUN),baseline_sha=head,branch=newbranch,
   original_files=len(inventory),checks=str(RUN/'checks.json')),ensure_ascii=False))
