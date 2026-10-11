"""Restore hash-checked small public evidence into a NEW directory only.

Each archive has its own namespace: historical and closing snapshots never
overwrite each other. Images, checkpoints and descriptor arrays stay local.
"""
import argparse,hashlib,json,stat,sys,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--destination',type=Path,required=True);ap.add_argument('--numeric-audit',action='store_true');args=ap.parse_args()
    target=args.destination.resolve();target.mkdir(parents=True,exist_ok=False);rows=[];restored={}
    for manifest in sorted((ROOT/'artifacts/v4').rglob('archive_manifest.json')):
        m=json.loads(manifest.read_text());archive=manifest.parent/'evidence.zip'
        assert digest(archive)==m['zip_sha256'] and archive.stat().st_size==m['zip_bytes'],str(archive)
        folder=target/m['run_id'];folder.mkdir(exist_ok=False);restored[m['run_id']]=folder;count=0
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names=set()
            for info in z.infolist():
                p=PurePosixPath(info.filename);mode=info.external_attr>>16
                assert not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename and info.filename not in names
                assert not stat.S_ISLNK(mode) and (stat.S_IFMT(mode) in (0,stat.S_IFREG,stat.S_IFDIR))
                names.add(info.filename);dest=folder.joinpath(*p.parts)
                if info.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
                dest.parent.mkdir(parents=True,exist_ok=True);payload=z.read(info);dest.write_bytes(payload)
                assert digest(dest)==hashlib.sha256(payload).hexdigest();count+=1
        rows.append(dict(run_id=m['run_id'],files=count,zip_sha256=m['zip_sha256'],restored_root=str(folder)))
    audits=[]
    if args.numeric_audit:
        sys.path.insert(0,str(Path(__file__).parent))
        from evaluation import audit_csv
        state=json.loads((ROOT/'docs/goals/GOAL_V4_STATE.json').read_text())
        for field in ['g2_run','g3_run','g4_run']:
            run_id=state[field];folder=restored[run_id]/'outputs_v4'/run_id
            metrics=json.loads((folder/'raw_metrics.json').read_text())['results']
            audits.append(dict(run_id=run_id,**audit_csv(folder/'per_query.csv',metrics)))
    result=dict(passed=True,archives=rows,numeric_audits=audits,originals_overwritten=False)
    (target/'restore_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,archives=len(rows),files=sum(r['files'] for r in rows),metric_groups=sum(a['metric_groups'] for a in audits))))
if __name__=='__main__':main()
