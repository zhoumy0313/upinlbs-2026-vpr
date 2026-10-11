"""Resume G0 only after actual official files exist. Never evaluates retrieval."""
import tarfile
from pathlib import PurePosixPath
from runtime import *
from download import SEQUENCES
def safe_members(members,expected_root):
    names=set()
    for m in members:
        p=PurePosixPath(m.name)
        if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!=expected_root:raise ValueError('Unsafe/out-of-root member: '+m.name)
        if '\\' in m.name or '\x00' in m.name:raise ValueError('Ambiguous path: '+m.name)
        if not (m.isfile() or m.isdir()):raise ValueError('Links/devices/other special files prohibited: '+m.name)
        if m.name in names:raise ValueError('Duplicate member: '+m.name)
        names.add(m.name)
    if not any(m.isfile() and m.name==expected_root+'/rgb.txt' for m in members):raise ValueError('rgb.txt missing')
    if not any(m.isfile() and m.name==expected_root+'/groundtruth.txt' for m in members):raise ValueError('groundtruth.txt missing')
    return members
def main():
    run=Run('g0_import',dict(purpose='official local archive audit, no retrieval; required before G1',source_audit_sha256=sha(ROOT/'docs/research_v4/SOURCE_AUDIT.md')))
    receipts=[]
    for seq,role in SEQUENCES:
        archive=ROOT/'data/raw/v4/tum_rgbd/archives'/('rgbd_dataset_'+seq+'.tgz')
        if not archive.is_file() or not archive.stat().st_size:
            receipts.append(dict(sequence=seq,role=role,status='missing_official_archive',path=str(archive)));continue
        identity=sha(archive);code=run.command(['tar','-tzf',str(archive)],allow_failure=True)
        if code:receipts.append(dict(sequence=seq,role=role,status='corrupt_archive',tar_exit_code=code,sha256=identity));continue
        with tarfile.open(archive,'r:gz') as tf:
            members=safe_members(tf.getmembers(),'rgbd_dataset_'+seq)
            target=ROOT/'data/raw/v4/tum_rgbd/extracted'/run.id/seq
            target.mkdir(parents=True,exist_ok=False)
            # All members are regular files/directories under one safe root; no overwrite.
            tf.extractall(target,members=members)
        image_root=target/('rgbd_dataset_'+seq)
        receipts.append(dict(sequence=seq,role=role,status='archive_extracted_safely',sha256=identity,archive_bytes=archive.stat().st_size,members=len(members),rgb_png_files=len(list((image_root/'rgb').glob('*.png'))),depth_png_files=len(list((image_root/'depth').glob('*.png'))),extracted_root=str(image_root),rgb_txt_sha256=sha(image_root/'rgb.txt'),groundtruth_txt_sha256=sha(image_root/'groundtruth.txt'),note='RGB decode/timestamp/GT association validation still required; G0 not accepted automatically'))
    write(run.path/'DATA_MANIFEST.json',dict(sequences=receipts,retrieval_evaluated=False))
    ready=all(r['status']=='archive_extracted_safely' for r in receipts)
    run.finish(dict(sequences=receipts,archives_extracted=ready,G0_scientific_acceptance=False),passed=False)
    print(json.dumps(dict(run_id=run.id,archives_extracted=ready,G1_not_executed=True)),flush=True)
    if not ready:sys.exit(2)
if __name__=='__main__':main()
