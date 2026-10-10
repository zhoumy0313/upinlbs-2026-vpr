"""Gallery encoding before freeze; independent query images are never encoded here."""
import argparse,json,sys,time,resource
from pathlib import Path
import numpy as np
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.encoders.frozen import create_encoder
from runtime import Run,digest,update_state

def worker(audit,path):
    path=Path(path);manifest=ROOT/'outputs_v2'/audit/'manifest.json';records=json.loads(manifest.read_text())['records']
    rows=[r for r in records if r['role']=='gallery'];info={}
    device='cuda' if torch.cuda.is_available() else 'cpu'
    for method in ['cosplace','eigenplaces','dinov2']:
        encoder=create_encoder(method,device,(224,224));torch.cuda.synchronize() if device=='cuda' else None
        start=time.perf_counter();out=[]
        if device=='cuda':torch.cuda.reset_peak_memory_stats()
        for i in range(0,len(rows),16):
            images=[]
            for r in rows[i:i+16]:
                with Image.open(ROOT/r['relative_path']) as im:images.append(im.convert('RGB'))
            out.append(encoder.encode(images))
        if device=='cuda':torch.cuda.synchronize()
        elapsed=time.perf_counter()-start;array=np.concatenate(out);assert array.shape==(len(rows),encoder.dimension)
        np.save(path/(method+'_gallery.npy'),array)
        info[method]=dict(gallery_image_ids=[r['image_id'] for r in rows],array_sha256=digest(path/(method+'_gallery.npy')),
            fingerprint=encoder.fingerprint(),offline_gallery_build_seconds=elapsed,batch_size=16,images=len(rows),
            descriptor_bytes=int(array.nbytes),peak_cuda_allocated_bytes=int(torch.cuda.max_memory_allocated()) if device=='cuda' else 0,
            process_highwater_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        print(method,len(rows),elapsed,flush=True);del encoder
        if device=='cuda':torch.cuda.empty_cache()
    (path/'gallery_identities.json').write_text(json.dumps(info,indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',required=True);p.add_argument('--worker');a=p.parse_args()
    if a.worker:worker(a.audit,a.worker);return
    audit=ROOT/'outputs_v2'/a.audit;assert json.loads((audit/'checks.json').read_text())['passed']
    run=Run(ROOT,'g4_gallery_build',dict(gallery_only=True,batch_size=16),dict(audit=a.audit,manifest_sha256=digest(audit/'manifest.json')))
    print(run.id,flush=True)
    run.command([str(ROOT/'.venv-p0/bin/python'),str(Path(__file__).resolve()),'--audit',a.audit,'--worker',str(run.path)],
        {'PYTHONPATH':'','TORCH_HOME':str(ROOT/'weights/p0_torch'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
    run.write('checks.json',dict(passed=True,independent_query_images_not_encoded=True,query_performance_unopened=True))
    run.write('metrics.json',json.loads((run.path/'gallery_identities.json').read_text()))
    (run.path/'per_query.csv').write_text('gallery_only\ntrue\n')
    (run.path/'interpretation.md').write_text('Offline gallery build, not online query latency. Encoder/preprocessing/cache arrays identified by exact hashes before independent performance.\n')
    update_state(ROOT,g4_audit_run=a.audit,g4_gallery_run=run.id,latest_run_id=run.id)
    print(json.dumps(dict(run=run.id)),flush=True)

if __name__=='__main__':main()
