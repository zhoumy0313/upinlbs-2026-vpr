import json,subprocess
from runtime import *
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0');files={ROOT/x.decode() for x in tracked if x}
    for name in ['outputs','outputs_v2','outputs_v3','paper','freezes','data','weights','cache','third_party']:
        files.update(p for p in (ROOT/name).rglob('*') if p.is_file() and not any(x in ['.git','__pycache__','v4'] for x in p.relative_to(ROOT).parts) and p.suffix!='.pyc')
    inventory=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
    write(ROOT/'artifacts/v4/g0/old_files.json',inventory)
    write(ROOT/'artifacts/v4/g0/input_receipt.json',dict(goal_sha256=sha(ROOT/'docs/goals/GOAL_V4_DATA_READY.md'),initial_git_status='?? docs/goals/GOAL_V4_DATA_READY.md',base_sha=BASE,old_files=len(inventory),old_bytes=sum(r['bytes'] for r in inventory)))
    shutil.copyfile(ROOT/'docs/goals/GOAL_V4_DATA_READY.md',ROOT/'artifacts/v4/g0/goal_input_original.md')
    with (ROOT/'.gitignore').open('ab') as f:f.write(b'\n# V4: raw images, models and arrays stay local; public numeric evidence only.\noutputs_v4/\n!artifacts/v4/**/*.zip\n')
    write(ROOT/'docs/goals/GOAL_V4_STATE.json',dict(goal_id='VPR-GOAL-V4',status='active',base_sha=BASE,branch=BRANCH,stages={f'g{i}':'pending' for i in range(7)},independent_retrieval_opened=False,positive_method_claim=False,formal_submission_ready=False))
    (ROOT/'docs/research_v4/PLAN.md').write_text('''# VPR-GOAL-V4 execution\n\nG0 preserve/download/audit → G1 timestamp/pose protocol → G2 strong baselines and 1/3/5Hz development → G3 bounded timestamp mechanism → G4 immutable freeze and one independent evaluation → G5 real images batch-one timing, three passes, paper → G6 replay/audit/archive.\n\nThe 09e7fb0 V3 base and every old scientific file remain unchanged; .gitignore may only append. TUM Pioneer is development and Long Office is independent. No old sequence becomes independent. No system or network reconfiguration. No training visual encoders. Human handles formal actions and author approval. Online kernels never receive GT. New innovation requires beating the strongest mature/simple comparator at strict radii, not only a weak old setting.\n''')
    run=Run('g0_bootstrap',dict(base=BASE,branch=BRANCH))
    for argv in [['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],['free','-h'],['df','-h',str(ROOT)],['codex','login','status'],['systemctl','is-active','ssh']]:run.command(argv)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','experiments/endpoint_vpr/tests','experiments/paper_v2/test_manuscript_audit.py','-q','--junitxml='+str(run.path/'regression.xml')],dict(PYTHONPATH='',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'))
    run.finish(dict(old_files=len(inventory),old_bytes=sum(r['bytes'] for r in inventory),legacy_regression='see XML actual counts',no_system_changes=True));run.checkpoint('G0 preservation startup')
if __name__=='__main__':main()
