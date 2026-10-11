"""Records actual whole-process exits and full Python stdout/stderr."""
from runtime import *
def main():
    filename=sys.argv[1]
    assert filename.startswith('run_') and '/' not in filename and filename.endswith('.py')
    run=Run('execution',dict(script=filename,args=sys.argv[2:],whole_process_capture=True))
    env=dict(PYTHONPATH='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',TORCH_HOME=str(ROOT/'weights/p0_torch'))
    code=run.command([str(ROOT/'.venv-p0/bin/python'),str(ROOT/'experiments/temporal_alignment_v4'/filename),*sys.argv[2:]],env,allow_failure=True)
    run.finish(dict(actual_whole_process_exit_code=code,script=filename),passed=code==0)
    print(json.dumps(dict(run_id=run.id,exit_code=code)),flush=True)
    sys.exit(code)
if __name__=='__main__':main()
