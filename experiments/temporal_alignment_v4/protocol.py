"""Offline-only RGB/pose metadata adapter. Never imported by online matcher."""
import csv,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from experiments.temporal_alignment_v4.runtime import ROOT,sha,write
RADII=[.25,.5,1.]
def lines(path):
    return [x.split() for x in Path(path).read_text().splitlines() if x.strip() and not x.lstrip().startswith('#')]
def nearest(times,value):
    k=np.searchsorted(times,value);options=[j for j in [k-1,k] if 0<=j<len(times)]
    return min(options,key=lambda j:(abs(times[j]-value),times[j]))
def sampled(rows,hz):
    first=rows[0]['timestamp'];seen=set();out=[]
    for r in rows:
        b=int(np.floor((r['timestamp']-first)*hz))
        if b not in seen:seen.add(b);out.append(r)
    return out
def construct(rows,hz=5):
    midpoint=(rows[0]['timestamp']+rows[-1]['timestamp'])/2
    selected=sampled(rows,hz)
    g=[r for r in selected if r['timestamp']<midpoint and r['valid_gt']]
    q=[r for r in selected if r['timestamp']>=midpoint+10]
    assert g and q and q[0]['timestamp']-g[-1]['timestamp']>=10
    return dict(g=g,q=q,midpoint=midpoint,hz=hz,source_rows=len(rows),sampled_rows=len(selected),excluded_buffer_or_other=len(selected)-len(g)-len(q))
def distances(d):
    g=np.array([r['xyz'] for r in d['g']]);q=np.array([r['xyz'] if r['valid_gt'] else [np.nan]*3 for r in d['q']])
    return np.linalg.norm(q[:,None,:]-g[None,:,:],axis=2)
def audit_sequence(receipt,run):
    seq=receipt['sequence'];role=receipt['role'];root=Path(receipt['extracted_root'])
    rgb=lines(root/'rgb.txt');poses=np.array([[float(x) for x in row] for row in lines(root/'groundtruth.txt')])
    assert poses.ndim==2 and poses.shape[1]==8 and np.isfinite(poses).all()
    assert (np.diff(poses[:,0])>=0).all(),'GT time reversal requires explicit audit'
    original_gt_count=len(poses)
    duplicate_indices=np.flatnonzero(np.diff(poses[:,0])==0)
    duplicate_records=[dict(source_rows=[int(i),int(i+1)],poses=poses[i:i+2].tolist(),translation_difference_m=float(np.linalg.norm(poses[i,1:4]-poses[i+1,1:4]))) for i in duplicate_indices]
    write(run.path/(seq+'_duplicate_gt_audit.json'),dict(policy='retain raw file/all duplicate evidence; nearest association uses first original row for each exact timestamp',records=duplicate_records))
    _,first_indices=np.unique(poses[:,0],return_index=True);poses=poses[np.sort(first_indices)]
    times=np.array([float(r[0]) for r in rgb]);assert (np.diff(times)>0).all()
    norms=np.linalg.norm(poses[:,4:],axis=1);assert np.max(np.abs(norms-1))<.01
    rows=[]
    for i,(timestamp,name) in enumerate(rgb):
        p=root/name;assert p.resolve().is_relative_to(root.resolve()) and p.is_file()
        with Image.open(p) as im:im.load();assert im.size==(640,480);im.convert('RGB')
        t=float(timestamp);k=nearest(poses[:,0],t);delta=abs(float(poses[k,0])-t);valid=delta<=.03
        rows.append(dict(sequence=seq,role=role,source_index=i,image_id=seq+'/'+name,timestamp=t,relative_path=str(p.relative_to(ROOT)),sha256=sha(p),valid_gt=valid,gt_status='valid_gt' if valid else 'invalid_gt',gt_timestamp=float(poses[k,0]),association_delta_seconds=delta,xyz=poses[k,1:4].tolist() if valid else None,quaternion_xyzw=poses[k,4:].tolist() if valid else None,split='gallery_period' if t<(times[0]+times[-1])/2 else 'query_period' if t>=(times[0]+times[-1])/2+10 else 'buffer'))
        if (i+1)%1000==0:print(seq,'audited',i+1,flush=True)
    path=ROOT/'data/manifests/v4'/(seq+'_all_rgb.json');assert not path.exists();write(path,rows)
    summary=dict(**receipt,rgb_count=len(rows),gt_count=original_gt_count,unique_gt_timestamps=len(poses),duplicate_gt_count=len(duplicate_indices),rgb_span_seconds=float(times[-1]-times[0]),gt_span_seconds=float(poses[-1,0]-poses[0,0]),rgb_first=float(times[0]),rgb_last=float(times[-1]),gt_first=float(poses[0,0]),gt_last=float(poses[-1,0]),valid_rgb_gt_matches=sum(r['valid_gt'] for r in rows),invalid_rgb_gt_matches=sum(not r['valid_gt'] for r in rows),all_rgb_decoded=True,quaternion_max_norm_error=float(np.max(abs(norms-1))),all_rgb_manifest=str(path.relative_to(ROOT)),all_rgb_manifest_sha256=sha(path),association_max_seconds=.03,association='nearest, earlier tie break, first original row for duplicate GT timestamps, many RGB can share GT; offline only',source_attestation='user transferred requested official archives; upstream independent published checksum not available')
    return rows,summary
def coverage(d):
    dist=distances(d);valid=np.array([r['valid_gt'] for r in d['q']]);out=[]
    for r in RADII:
        closed=(dist<=r).any(axis=1)&valid
        out.append(dict(radius_m=r,total_queries=len(d['q']),valid_gt_queries=int(valid.sum()),invalid_gt_queries=int((~valid).sum()),closed_queries=int(closed.sum()),open_queries=int((valid&~closed).sum()),closed_coverage=float(closed.sum()/valid.sum()) if valid.any() else None,nearest_gallery_distance_median=float(np.nanmedian(np.min(dist,axis=1))),nearest_gallery_distance_P90=float(np.nanpercentile(np.min(dist,axis=1),90))))
    return out
def load(seq,hz=5):
    rows=json.loads((ROOT/'data/manifests/v4'/(seq+'_all_rgb.json')).read_text());d=construct(rows,hz);d.update(sequence=seq,role=rows[0]['role']);return d
