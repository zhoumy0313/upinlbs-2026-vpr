"""Actual RGB extraction; role and full fingerprints bound to row identities."""
import sys,time,json
import numpy as np
import torch
from PIL import Image
from runtime import ROOT,sha,write
from protocol import load
sys.path.insert(0,str(ROOT/'src'))
from vpr_research.encoders.frozen import create_encoder
def sync():
    if torch.cuda.is_available():torch.cuda.synchronize()
def encode(seq,hzs,run):
    rows={r['image_id']:r for hz in hzs for r in load(seq,hz)['g']+load(seq,hz)['q']};rows=sorted(rows.values(),key=lambda r:r['timestamp'])
    write(run.path/'descriptor_rows.json',[dict(image_id=r['image_id'],timestamp=r['timestamp'],relative_path=r['relative_path'],image_sha256=r['sha256'],sequence=r['sequence'],role=r['role']) for r in rows])
    fingerprints={};cost=[]
    for name in ['cosplace','eigenplaces']:
        start=time.perf_counter();encoder=create_encoder(name,'cuda' if torch.cuda.is_available() else 'cpu',(224,224));sync();load_s=time.perf_counter()-start
        fingerprints[name]=encoder.fingerprint();arrays=[];start=time.perf_counter()
        for j in range(0,len(rows),16):
            ims=[]
            for r in rows[j:j+16]:
                p=ROOT/r['relative_path'];assert sha(p)==r['sha256']
                with Image.open(p) as im:ims.append(im.convert('RGB'))
            arrays.append(encoder.encode(ims))
        sync();seconds=time.perf_counter()-start;f=np.concatenate(arrays);assert f.shape==(len(rows),512);np.save(run.path/(name+'_descriptors.npy'),f)
        cost.append(dict(encoder=name,images=len(rows),batch_size=16,model_load_seconds=load_s,decode_preprocess_encode_seconds=seconds,array_sha256=sha(run.path/(name+'_descriptors.npy')),array_bytes=(run.path/(name+'_descriptors.npy')).stat().st_size))
        print(name,'encoded',len(rows),'seconds',seconds,flush=True);del encoder
        if torch.cuda.is_available():torch.cuda.empty_cache()
    write(run.path/'model_identity.json',fingerprints);write(run.path/'feature_manifest.json',dict(sequence=seq,hzs=hzs,descriptor_rows_sha256=sha(run.path/'descriptor_rows.json'),model_identity_sha256=sha(run.path/'model_identity.json'),full_input_manifest_sha256=sha(ROOT/'data/manifests/v4'/(seq+'_all_rgb.json')),preprocessing_hw=[224,224],cost=cost,cache_accuracy_only=True))
    return cost
def with_scores(seq,hz,folder):
    folder=ROOT/folder if not __import__('pathlib').Path(folder).is_absolute() else __import__('pathlib').Path(folder)
    info=json.loads((folder/'feature_manifest.json').read_text());assert info['sequence']==seq and hz in info['hzs']
    assert sha(folder/'descriptor_rows.json')==info['descriptor_rows_sha256'] and sha(folder/'model_identity.json')==info['model_identity_sha256']
    assert sha(ROOT/'data/manifests/v4'/(seq+'_all_rgb.json'))==info['full_input_manifest_sha256']
    rows=json.loads((folder/'descriptor_rows.json').read_text());ids={r['image_id']:i for i,r in enumerate(rows)};d=load(seq,hz);d['scores']={}
    for record in info['cost']:
        name=record['encoder'];p=folder/(name+'_descriptors.npy');assert sha(p)==record['array_sha256'];f=np.load(p).astype(np.float64);f/=np.linalg.norm(f,axis=1,keepdims=True)
        g=f[[ids[r['image_id']] for r in d['g']]];q=f[[ids[r['image_id']] for r in d['q']]];d['scores'][name]=np.clip(q@g.T,-1,1)
    return d
