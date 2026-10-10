import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

path = Path(__file__).resolve().parents[1]/'runtime.py'
spec = importlib.util.spec_from_file_location('v2_runtime',path)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

def test_atomic_invalid_value_does_not_replace_state(tmp_path):
    path = tmp_path/'state.json'
    runtime.atomic_json(path,{'stage':'G0'})
    with pytest.raises(ValueError):
        runtime.atomic_json(path,{'metric':float('nan')})
    assert json.loads(path.read_text()) == {'stage':'G0'}

def test_run_collision_failure_logging_and_environment_are_safe(tmp_path):
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    subprocess.run(['git','-C',str(tmp_path),'-c','user.name=test','-c','user.email=test@localhost',
                    'commit','--allow-empty','-qm','synthetic runtime fixture'],check=True)
    run = runtime.Run(tmp_path,'unit',{}, {},run_id='same')
    with pytest.raises(FileExistsError):
        runtime.Run(tmp_path,'unit',{}, {},run_id='same')
    with pytest.raises(ValueError):
        run.command(['true'],{'API_KEY':'NEVER_LOG'})
    assert 'NEVER_LOG' not in (run.path/'argv.json').read_text()
    assert run.command([sys.executable,'-c','import sys;print("out");print("err",file=sys.stderr);sys.exit(7)'],allow_failure=True)==7
    assert 'out' in (run.path/'stdout.log').read_text()
    assert 'err' in (run.path/'stderr.log').read_text()
    assert json.loads((run.path/'commands.jsonl').read_text())['exit_code']==7

def test_g0_snapshot_goal_and_historical_science_match():
    root = Path(__file__).resolve().parents[3]
    baseline = json.loads((root/'docs/goals/v1_baseline_state.json').read_text())
    for rel,expected in baseline['preserved_hashes'].items():
        assert runtime.digest(root/rel)==expected
    assert runtime.digest(root/'docs/goals/GOAL_V2_TEMPORAL_VPR.md')==baseline['original_goal_sha256']
    for name in ['main.tex','main.pdf','references.bib']:
        assert runtime.digest(root/'paper/versions/v1_20261010_frozen'/name)==runtime.digest(root/'paper'/name)
    assert subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip()==baseline['baseline_sha']
