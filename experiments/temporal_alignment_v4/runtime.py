"""V4 only provenance, preservation and Git checkpoints."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,uuid,zipfile,shutil,traceback
ROOT=Path(__file__).resolve().parents[2]
BASE='09e7fb0fc63489817a09901fda37ae9896a9c404'
BRANCH='research/vpr-v4-temporal-alignment'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def preserve():
    rows=json.loads((ROOT/'artifacts/v4/g0/old_files.json').read_text())
    errors=[]
    for r in rows:
        p=ROOT/r['path']
        actual=hashlib.sha256(p.read_bytes()[:r['bytes']]).hexdigest() if r['path']=='.gitignore' else sha(p) if p.is_file() else None
        if actual!=r['sha256']:errors.append(r['path'])
    if errors:raise RuntimeError('Old asset changed: '+str(errors))
    return len(rows)
class Run:
    def __init__(self,stage,config):
        self.id=stage+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
        self.path=ROOT/'outputs_v4'/self.id;self.path.mkdir(parents=True,exist_ok=False)
        write(self.path/'run_config.yaml',config)
        write(self.path/'run_meta.json',dict(run_id=self.id,utc=utc(),parent_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),argv=sys.argv,cwd=str(ROOT),environment={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','TORCH_HOME','PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD']}))
        for p in (ROOT/'experiments/temporal_alignment_v4').rglob('*'):
            if p.is_file() and p.suffix in ['.py','.md']:
                dest=self.path/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        for n in ['stdout.log','stderr.log','commands.jsonl','failures.jsonl']:(self.path/n).touch()
        def hook(kind,error,tb):
            with (self.path/'stderr.log').open('a') as f:traceback.print_exception(kind,error,tb,file=f)
            write(self.path/'process_failure.json',dict(type=kind.__name__,error=str(error),exit_code=1))
            sys.__excepthook__(kind,error,tb)
        sys.excepthook=hook
        print(self.id,flush=True)
    def command(self,argv,env=None,allow_failure=False):
        env=env or {};row=dict(argv=list(map(str,argv)),cwd=str(ROOT),started_utc=utc(),environment_overrides=env)
        with (self.path/'stdout.log').open('a') as out,(self.path/'stderr.log').open('a') as err:
            p=subprocess.run(row['argv'],cwd=ROOT,env={**os.environ,**env},stdout=out,stderr=err)
        row.update(exit_code=p.returncode,ended_utc=utc())
        with (self.path/'commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        if p.returncode:
            with (self.path/'failures.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            if not allow_failure:raise subprocess.CalledProcessError(p.returncode,argv)
        return p.returncode
    def finish(self,metrics,passed=True):
        write(self.path/'raw_metrics.json',metrics);write(self.path/'acceptance.json',dict(passed=passed,ended_utc=utc()))
        (self.path/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(self.path).as_posix()+'\n' for p in sorted(self.path.rglob('*')) if p.is_file()))
        stage=self.id.split('_')[0];pub=ROOT/'artifacts/v4'/stage/self.id;pub.mkdir(parents=True,exist_ok=False)
        with zipfile.ZipFile(pub/'evidence.zip','x',zipfile.ZIP_LZMA) as z:
            for p in sorted(self.path.rglob('*')):
                if p.is_file() and p.suffix in ['.py','.md','.json','.jsonl','.yaml','.csv','.log','.xml','.txt','.actual']:z.write(p,p.relative_to(ROOT))
            assert z.testzip() is None
        assert (pub/'evidence.zip').stat().st_size<90*1024**2
        write(pub/'archive_manifest.json',dict(run_id=self.id,zip_sha256=sha(pub/'evidence.zip'),zip_bytes=(pub/'evidence.zip').stat().st_size))
        write(pub/'raw_metrics.json',metrics)
        st=ROOT/'docs/goals/GOAL_V4_STATE.json';s=json.loads(st.read_text());s['latest_run_id']=self.id;s['updated_utc']=utc()
        if passed and stage in s['stages']:s['stages'][stage]='passed'
        write(st,s)
    def checkpoint(self,label):
        assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==BRANCH
        count=preserve();write(self.path/'preservation_before_checkpoint.json',dict(old_files=count,passed=True))
        paths=['experiments/temporal_alignment_v4','configs/v4','docs/research_v4','docs/goals/GOAL_V4_DATA_READY.md','docs/goals/GOAL_V4_STATE.json','artifacts/v4','data/manifests/v4','.gitignore']
        paths += [str(p.relative_to(ROOT)) for p in (ROOT/'paper/revisions').glob('v4_*')]
        paths += [str(p.relative_to(ROOT)) for p in (ROOT/'freezes').glob('v4_*')]
        paths += [str(p.relative_to(ROOT)) for p in (ROOT/'.github/workflows').glob('v4*')]
        self.command(['git','add',*paths])
        for f in subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0'):
            if f:assert (ROOT/f.decode()).stat().st_size<100*1024**2,f
        self.command(['git','-c','user.name=Codex','-c','user.email=codex@localhost','commit','-m',label+': VPR-GOAL-V4 checkpoint'])
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        code=self.command(['git','push','-u','origin',BRANCH],allow_failure=True)
        write(self.path/'checkpoint_receipt.json',dict(commit=commit,push_exit_code=code,old_files_preserved=count))
        if code:raise RuntimeError('Push failed; preserved receipt')
