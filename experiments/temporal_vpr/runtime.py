"""Append-only experiment commands and atomically validated persistent state."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        temporary.write_text(serialized)
        assert json.loads(temporary.read_text()) == value
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

class Run:
    def __init__(self, root, task, config, inputs, run_id=None):
        self.root = Path(root).resolve()
        self.id = run_id or task + '_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
        self.path = self.root / 'outputs_v2' / self.id
        self.path.mkdir(parents=True, exist_ok=False)
        (self.path / 'figures').mkdir()
        source_files=sorted((self.root/'experiments/temporal_vpr').rglob('*.py'))
        for source in source_files:
            snapshot=self.path/'source_snapshot'/source.relative_to(self.root)
            snapshot.parent.mkdir(parents=True,exist_ok=True)
            snapshot.write_bytes(source.read_bytes())
        self.commands = []
        self.write('run_manifest.json', dict(run_id=self.id, task=task, started_utc=utc_now(),
            git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=self.root,text=True).strip(),
            source_sha256={p.relative_to(self.root).as_posix():digest(p) for p in
                sorted((self.root/'experiments/temporal_vpr').rglob('*.py'))},
            independent_performance_opened=False, config_sha256=hashlib.sha256(
                json.dumps(config,sort_keys=True,allow_nan=False).encode()).hexdigest()))
        self.write('config_effective.yaml', config) # JSON is a valid YAML subset.
        self.write('inputs.json', inputs)
        self.write('argv.json', dict(entrypoint_argv=sys.argv,commands=[], cwd=str(self.root), environment_overrides={}))
        for filename in ['commands.jsonl','stdout.log','stderr.log']:
            (self.path/filename).touch(exist_ok=False)

    def write(self, filename, value):
        destination = self.path / filename
        if destination.exists():
            raise FileExistsError(destination)
        atomic_json(destination, value)

    def command(self, argv, environment=None, allow_failure=False):
        environment = environment or {}
        # Only these harmless explicit overrides may be logged. Never dump environment.
        allowed = {'PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS',
                   'MPLCONFIGDIR','CUDA_VISIBLE_DEVICES','TORCH_HOME'}
        if set(environment) - allowed:
            raise ValueError('Unreviewed environment override; no credentials in logs')
        row = dict(argv=[str(a) for a in argv], cwd=str(self.root),
            environment_overrides=environment, started_utc=utc_now())
        with (self.path/'stdout.log').open('a') as out, (self.path/'stderr.log').open('a') as err:
            out.write('\nCOMMAND '+json.dumps(row['argv'])+'\n'); out.flush()
            err.write('\nCOMMAND '+json.dumps(row['argv'])+'\n'); err.flush()
            result = subprocess.run(row['argv'],cwd=self.root,env={**os.environ,**environment},stdout=out,stderr=err)
        row.update(ended_utc=utc_now(),exit_code=result.returncode)
        self.commands.append(row)
        with (self.path/'commands.jsonl').open('a') as f:
            f.write(json.dumps(row)+'\n')
        atomic_json(self.path/'argv.json',dict(entrypoint_argv=sys.argv,commands=self.commands,cwd=str(self.root)))
        if result.returncode and not allow_failure:
            self.write('command_failure_'+str(len(self.commands))+'.json',row)
            raise subprocess.CalledProcessError(result.returncode,row['argv'])
        return result.returncode

    def event(self, name, data):
        with (self.path/'commands.jsonl').open('a') as f:
            f.write(json.dumps(dict(event=name,utc=utc_now(),data=data),allow_nan=False)+'\n')

def update_state(root, **changes):
    path = Path(root)/'docs/goals/GOAL_V2_STATE.json'
    state = json.loads(path.read_text())
    state.update(changes, updated_utc=utc_now())
    assert state['goal_id']=='VPR-GOAL-V2'
    assert set(state['stages'])=={'G0','G1','G2','G3','G4','G5'}
    atomic_json(path,state)
    return state
