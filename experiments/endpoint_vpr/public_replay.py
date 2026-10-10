"""Portable frozen numerical evidence, without images/weights or latency claims."""
import argparse, json, zipfile, shutil
from pathlib import Path
import numpy as np
from .runtime import ROOT, Run, state, sha, atomic
from .datasets import seen
from .baselines import predictions, strong_specs, local_specs
from .evaluate import evaluate, record, audit_csv

def pack():
    run = Run('g7_numerical_inputs', 'archive one canonical frozen numerical input per seen route',
              dict(no_images_or_weights=True,no_descriptors=True,cached_accuracy_only=True))
    print(run.id,flush=True)
    bundle=[]
    for d in seen():
        if d['dataset']=='St_Lucia' and d['split']!='descriptive':
            continue
        stem=d['dataset']+'_'+d['split']
        entry={k:d[k] for k in ['dataset','split','q','g','radii','primary','unit','model_identity','manifest_sha256']}
        entry['scores']={}
        for name,array in d['scores'].items():
            p=run.path/(stem+'_'+name+'.npy')
            np.save(p,array)
            entry['scores'][name]=dict(file=p.name,sha256=sha(p),shape=list(array.shape),dtype=str(array.dtype))
        bundle.append(entry)
    run.write('bundle.json',dict(data_role='already_seen',accuracy_only=True,datasets=bundle))
    run.write('model_identity.json',{x['dataset']+'_'+x['split']:x['model_identity'] for x in bundle})
    run.finish(dict(unique_routes=len(bundle),no_new_model_inference=True),dict(passed=True))
    zpath=run.path/'numerical_inputs.zip'
    with zipfile.ZipFile(zpath,'x',zipfile.ZIP_LZMA) as z:
        for p in sorted(run.path.iterdir()):
            if p.suffix=='.npy' or p.name in ['bundle.json','model_identity.json','raw_metrics.json','acceptance.json']:
                z.write(p,p.name)
        assert z.testzip() is None
    public=ROOT/'artifacts/v3/replay_inputs'
    public.mkdir(exist_ok=False)
    limit=48*1024*1024
    parts=[]
    if zpath.stat().st_size<=limit:
        p=public/'evidence.zip';shutil.copyfile(zpath,p)
        parts.append(dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)))
    else:
        with zpath.open('rb') as src:
            i=0
            while b:=src.read(limit):
                i+=1;p=public/f'evidence.zip.part{i:03d}';p.write_bytes(b)
                parts.append(dict(name=p.name,bytes=len(b),sha256=sha(p)))
    atomic(public/'archive_manifest.json',dict(format='ordered_byte_concatenation_of_standard_zip',
        zip_sha256=sha(zpath),zip_bytes=zpath.stat().st_size,parts=parts,scientific_run=run.id,
        scope='derived numeric scores and evaluation IDs/metadata only; no photos/descriptors/checkpoints'))
    print(json.dumps(dict(run_id=run.id,zip_bytes=zpath.stat().st_size,parts=len(parts))),flush=True)

def replay(args):
    zpath=Path(args.archive).resolve()
    digest=sha(zpath)
    public=json.loads((ROOT/'artifacts/v3/replay_inputs/archive_manifest.json').read_text())
    assert digest==public['zip_sha256']
    freeze=json.loads((ROOT/state()['freeze_directory']/'freeze.json').read_text())
    # Archive SHA authenticates the derived dataset payload. A fresh clone needs
    # no original photos, checkpoints or V2 local cache/manifest paths.
    for rel,h in freeze['science_file_sha256'].items():
        if rel.startswith(('experiments/endpoint_vpr/','configs/v3/','src/')):
            assert sha(ROOT/rel)==h,rel
    run=Run('public_numeric_replay','replay public fixed scores, no images/model runtime or new test',
            dict(dataset=args.dataset,split=args.split,suite=args.suite,archive_sha256=digest,
                 cached_accuracy_only=True,online_latency_not_measured=True))
    with zipfile.ZipFile(zpath) as z:
        b=json.loads(z.read('bundle.json'))
        orig=next(x for x in b['datasets'] if x['dataset']==args.dataset and
                  x['split']==('descriptive' if args.dataset=='St_Lucia' else args.split))
        d=dict(orig);d['scores']={}
        import io, hashlib
        for name,x in orig['scores'].items():
            raw=z.read(x['file']);assert hashlib.sha256(raw).hexdigest()==x['sha256']
            a=np.load(io.BytesIO(raw),allow_pickle=False)
            assert list(a.shape)==x['shape'] and str(a.dtype)==x['dtype'] and np.isfinite(a).all()
            d['scores'][name]=a
    if args.dataset=='St_Lucia':
        lo,hi=(0,700) if args.split=='train' else (800,1464)
        d['q']=d['q'][lo:hi];d['scores']={k:v[lo:hi] for k,v in d['scores'].items()}
        q=np.array([[x['easting'],x['northing']] for x in d['q']]);g=np.array([[x['easting'],x['northing']] for x in d['g']])
        d['distance']=np.linalg.norm(q[:,None,:]-g[None,:,:],axis=-1)
    else:
        d['distance']=np.abs(np.array([x['frame_index'] for x in d['q']])[:,None]-np.array([x['frame_index'] for x in d['g']])[None,:])
    d['split']=args.split
    if args.suite=='grid':specs=local_specs()
    elif args.suite=='baselines':specs=strong_specs()
    else:
        wanted={'A','fixed_L9','full_L3'}|{x['name'] for x in freeze['selection']['selected'].values()}
        specs=[x for x in freeze['methods'] if x['name'] in wanted]
    metrics=[]
    with (run.path/'per_query.csv').open('w',newline='') as f:
        writer=None
        for spec in specs:
            ranks,meta=predictions(d,spec);m,rows=evaluate(d,spec,ranks,meta)
            metrics+=m;writer=record(f,writer,rows)
    checks=audit_csv(run.path/'per_query.csv',metrics)
    run.write('model_identity.json',d['model_identity'])
    run.write('input_manifest.json.actual',dict(query=d['q'],gallery=d['g'],source_archive_sha256=digest))
    run.finish(dict(results=metrics,audit=checks,online_latency='not_measured'),dict(passed=True))
    print(json.dumps(dict(run_id=run.id,methods=len(specs),groups=len(metrics))),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pack',action='store_true');p.add_argument('--archive')
    p.add_argument('--dataset',choices=['St_Lucia','Nordland'],default='St_Lucia')
    p.add_argument('--split',choices=['train','validation'],default='validation')
    p.add_argument('--suite',choices=['selected','baselines','grid'],default='selected')
    a=p.parse_args()
    if a.pack:pack()
    else:assert a.archive,'Restored archive required';replay(a)
