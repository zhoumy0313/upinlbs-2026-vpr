"""Record the real exit code of a whole stage, including publication/checkpoint."""
import sys,json
from .runtime import ROOT,Run

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: python -m experiments.endpoint_vpr.driver experiments.endpoint_vpr.run_g4')
    module=sys.argv[1]
    if not module.startswith('experiments.endpoint_vpr.'):raise ValueError('V3 modules only')
    run=Run('stage_driver','whole-stage subprocess exit receipt',dict(module=module));print(run.id,flush=True)
    code=run.command([str(ROOT/'.venv-p0/bin/python'),'-m',module],env={'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'},allow_failure=True);run.write('model_identity.json',dict(not_applicable='Child stage model identities are separate'));run.finish(dict(module=module,actual_whole_stage_exit_code=code),dict(passed=code==0));print(json.dumps(dict(driver=run.id,module=module,actual_exit_code=code)),flush=True);return code
if __name__=='__main__':sys.exit(main())
