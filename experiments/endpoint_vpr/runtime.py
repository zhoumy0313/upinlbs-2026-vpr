"""V3-only append-only commands, snapshots, atomic state and checkpoint evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,traceback,uuid,zipfile,re
ROOT=Path(__file__).resolve().parents[2]
BASE='81fbf62dfaf5cdd28a005afbe6853289524b4d4d'
BRANCH='research/vpr-v3-endpoint-refinement'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def atomic(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex)
    s=json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n';t.write_text(s);assert json.loads(t.read_text())==d;os.replace(t,p)
def state(**changes):
    p=ROOT/'docs/goals/GOAL_V3_STATE.json';d=json.loads(p.read_text());d.update(changes,updated_utc=utc());atomic(p,d);return d
class Run:
    def __init__(self,stage,purpose,config,inputs=None):
        self.id=stage+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
        self.path=ROOT/'outputs_v3'/self.id;self.path.mkdir(parents=True,exist_ok=False);(self.path/'figures').mkdir()
        self.write('run_meta.json',dict(run_id=self.id,stage=stage,purpose=purpose,started_utc=utc(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),entrypoint_argv=sys.argv))
        self.write('config_effective.yaml',config);self.write('input_manifest.json',inputs or {})
        for p in sorted((ROOT/'experiments/endpoint_vpr').rglob('*.py')):
            t=self.path/'source_snapshot'/p.relative_to(ROOT);t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(p.read_bytes())
        for n in ['stdout.log','stderr.log','command_log.jsonl','failures.md']:(self.path/n).touch(exist_ok=False)
        def hook(kind,error,tb):
            with (self.path/'stderr.log').open('a') as f:traceback.print_exception(kind,error,tb,file=f)
            self.event('uncaught_exception',dict(type=kind.__name__,error=str(error),actual_exit_code=1));sys.__excepthook__(kind,error,tb)
        sys.excepthook=hook
    def write(self,name,d):
        p=self.path/name
        if p.exists():raise FileExistsError(p)
        atomic(p,d)
    def event(self,name,d):
        with (self.path/'command_log.jsonl').open('a') as f:f.write(json.dumps(dict(event=name,utc=utc(),data=d),allow_nan=False)+'\n')
    def command(self,argv,env=None,allow_failure=False):
        env=env or {};assert set(env)<=set(['PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','TORCH_HOME','MPLCONFIGDIR'])
        row=dict(argv=list(map(str,argv)),cwd=str(ROOT),environment_overrides=env,started_utc=utc(),stdout='stdout.log',stderr='stderr.log')
        with (self.path/'stdout.log').open('a') as out,(self.path/'stderr.log').open('a') as err:
            out.write('\nCOMMAND '+json.dumps(row['argv'])+'\n');out.flush();err.write('\nCOMMAND '+json.dumps(row['argv'])+'\n');err.flush()
            p=subprocess.run(row['argv'],cwd=ROOT,env={**os.environ,**env},stdout=out,stderr=err)
        row.update(exit_code=p.returncode,ended_utc=utc());self.event('command',row)
        if p.returncode:
            with (self.path/'failures.md').open('a') as f:f.write(json.dumps(row)+'\n')
            if not allow_failure:raise subprocess.CalledProcessError(p.returncode,argv)
        return p.returncode
    def finish(self,metrics,checks):
        self.write('raw_metrics.json',metrics);self.write('acceptance.json',checks)
        if not (self.path/'per_query.csv').exists():(self.path/'per_query.csv').write_text('run_id,status\n'+self.id+','+('pass' if checks.get('passed') else 'not_passed')+'\n')
        self.write('completion.json',dict(ended_utc=utc(),checks=checks))
        (self.path/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(self.path).as_posix()+'\n' for p in sorted(self.path.rglob('*')) if p.is_file()))
def preserve_check():
    p=ROOT/'artifacts/v3/g0/old_files.json';rows=json.loads(p.read_text());errors=[]
    for r in rows:
        f=ROOT/r['path']
        if r['path']=='.gitignore':actual=hashlib.sha256(f.read_bytes()[:r['bytes']]).hexdigest()
        else:actual=sha(f) if f.exists() else None
        if actual!=r['sha256']:errors.append(r['path'])
    if errors:raise RuntimeError('BLOCKED_PRESERVE_OLD: '+str(errors))
    return len(rows)
def publish(stage,run,report):
    public=ROOT/'artifacts/v3'/stage;public.mkdir(parents=True,exist_ok=False)
    text_ext={'.py','.json','.jsonl','.log','.csv','.xml','.yaml','.md','.txt'}
    with zipfile.ZipFile(public/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run.path.rglob('*')):
            if p.is_file() and p.suffix in text_ext and 'reading' not in p.parts:z.write(p,p.relative_to(ROOT).as_posix())
        assert z.testzip() is None
    for name in ['raw_metrics.json','acceptance.json']:(public/name).write_bytes((run.path/name).read_bytes())
    (public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    (ROOT/'docs/research_v3'/('G'+stage.removeprefix('g')+'_ACCEPTANCE.md')).write_text(report+'\n\nRun '+run.id+'; archive SHA '+sha(public/'evidence.zip')+'; exact commands/exits/logs in the public archive. Checkpoint follows this report; push receipt is recorded separately.\n')
def checkpoint(stage):
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==BRANCH
    run=Run(stage+'_checkpoint','authorized V3 branch backup',{},{});preserve_check()
    paths=['experiments/endpoint_vpr','configs/v3','docs/research_v3','docs/goals/GOAL_V3_ENDPOINT_REFINEMENT.md','docs/goals/GOAL_V3_STATE.json','artifacts/v3','.gitignore']
    paths += [str(p.relative_to(ROOT)) for p in (ROOT/'paper/revisions').glob('v3_*')]
    paths += [str(p.relative_to(ROOT)) for p in (ROOT/'freezes').glob('v3_*')]
    run.command(['git','add',*paths])
    for f in subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0'):
        if not f:continue
        p=ROOT/f.decode();assert p.stat().st_size<100*1024**2,p
        if p.suffix in ['.py','.md','.json','.yaml','.txt','.log']:
            s=p.read_text(errors='replace');assert not re.search(r'-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----\n',s),p
            assert not re.search(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{25,})\b',s),p
    run.command(['git','-c','user.name=Codex','-c','user.email=codex@localhost','commit','-m',stage+': VPR-GOAL-V3 checkpoint'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();code=run.command(['git','push','origin',BRANCH],allow_failure=True)
    run.finish(dict(commit=commit,pushed=code==0),dict(passed=code==0,old_files_preserved=True))
    if code==0:state(last_pushed_sha=commit)
    print(json.dumps(dict(run=run.id,commit=commit,pushed=code==0)),flush=True)
