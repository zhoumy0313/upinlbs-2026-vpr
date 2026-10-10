"""Public original evidence only; checkpoint on the V2 branch without rewriting history."""
import argparse,json,shutil,subprocess,zipfile,re
from pathlib import Path
from runtime import Run,digest,update_state
ROOT=Path(__file__).resolve().parents[2]
TEXT={'.json','.jsonl','.csv','.yaml','.xml','.log','.md','.py'}

def archive(stage,folders,selected):
    public=ROOT/'artifacts/v2'/stage;public.mkdir(parents=True,exist_ok=False)
    for source in selected:
        source=Path(source);target=public/source.name
        if target.exists():raise FileExistsError(target)
        shutil.copy2(source,target)
    with zipfile.ZipFile(public/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
        for folder in folders:
            for p in sorted(Path(folder).rglob('*')):
                if p.is_file() and p.suffix in TEXT and 'reading' not in p.parts and 'source_snapshot' not in p.parts:
                    z.write(p,p.relative_to(ROOT).as_posix())
        # Authored code; copyrighted external articles and third-party source omitted.
        for p in sorted((ROOT/'experiments/temporal_vpr').rglob('*.py')):z.write(p,p.relative_to(ROOT).as_posix())
    (public/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    return public

def checkpoint(stage):
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='research/temporal-vpr-v2'
    run=Run(ROOT,stage+'_checkpoint',dict(stage=stage,remote_backup=True),{})
    run.command(['git','add','AGENTS_V2.md','docs/goals','docs/research_v2','configs/v2','experiments/temporal_vpr','artifacts/v2','paper/revisions'] if (ROOT/'paper/revisions').exists() else
                ['git','add','AGENTS_V2.md','docs/goals','docs/research_v2','configs/v2','experiments/temporal_vpr','artifacts/v2'])
    if (ROOT/'freezes').exists():run.command(['git','add','freezes'])
    files=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0')
    for name in files:
        if name:
            p=ROOT/name.decode();assert p.stat().st_size<100*1024**2,p
            if p.suffix in TEXT:
                text=p.read_text(errors='replace')
                assert not re.search(r'-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----\n',text),p
                assert not re.search(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{25,})\b',text),p
    run.command(['git','-c','user.name=Codex','-c','user.email=codex@localhost','commit','-m',f'{stage}: VPR-GOAL-V2 reproducible checkpoint'])
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    run.command(['git','push','origin','research/temporal-vpr-v2'])
    run.write('metrics.json',dict(commit=sha,pushed=True));run.write('checks.json',dict(passed=True,all_staged_files_below_100MiB=True,main_unchanged=True))
    (run.path/'per_query.csv').write_text('commit,pushed\n'+sha+',true\n')
    (run.path/'interpretation.md').write_text('Backup of new V2 branch; main and frozen V1 tag retained.\n')
    print(json.dumps(dict(run=run.id,commit=sha,pushed=True)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');a=p.parse_args();checkpoint(a.stage)
