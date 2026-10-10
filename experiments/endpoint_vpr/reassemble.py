"""Restore an exact evidence ZIP from size-limited Git parts; refuse overwrite."""
import argparse,json,zipfile
from pathlib import Path
from .runtime import sha

def restore(folder,destination):
    folder=Path(folder);destination=Path(destination);m=json.loads((folder/'archive_manifest.json').read_text());destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as out:
        for part in m['parts']:
            p=folder/part['name'];assert p.parent==folder and p.stat().st_size==part['bytes'];assert sha(p)==part['sha256']
            with p.open('rb') as source:
                while b:=source.read(1024*1024):out.write(b)
    assert destination.stat().st_size==m['zip_bytes'] and sha(destination)==m['zip_sha256']
    with zipfile.ZipFile(destination) as z:assert z.testzip() is None
    return dict(restored=str(destination),sha256=sha(destination),bytes=destination.stat().st_size,passed=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('archive_folder');p.add_argument('destination');a=p.parse_args();print(json.dumps(restore(a.archive_folder,a.destination)))
if __name__=='__main__':main()
