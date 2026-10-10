"""Download and audit metadata only; never inspect retrieval performance before freeze."""
import csv,json,re,collections
from pathlib import Path
import numpy as np
from PIL import Image
from runtime import Run,digest,update_state
ROOT=Path(__file__).resolve().parents[2]
URL='rsync://vandaldata.polito.it/sf_xl/VPR-datasets-downloader/st_lucia/'

def parse_name(path):
    f=Path(path).name.split('@');session,frame=f[7].rsplit('_',1)
    return dict(easting=float(f[1]),northing=float(f[2]),zone=f[3]+f[4],latitude=float(f[5]),longitude=float(f[6]),
        traversal=session,source_frame=int(frame),timestamp_field=f[13])

def main():
    listing=ROOT/'outputs_v2/g1_independent_metadata_20261010T132115Z_756b6ce2/stdout.log'
    files=[re.split(r'\s+',l.strip(),maxsplit=4) for l in listing.read_text().splitlines() if l.startswith('-')]
    size=sum(int(r[1].replace(',','')) for r in files);assert size<30*1024**3
    run=Run(ROOT,'g4_independent_data_audit',dict(source=URL,metadata_only=True,max_download_bytes=30*1024**3,
        primary_radius_m=25,sensitivity_radius_m=[10,50],threshold_source='CosPlace parser.py positive_dist_threshold=25; adapted closed-set protocol'),
        dict(listing_sha256=digest(listing),listed_bytes=size,downloader_commit='2f886d53996d2a4cf549696c5e845c40d77da610'))
    print(run.id,flush=True);update_state(ROOT,latest_run_id=run.id)
    destination=ROOT/'data/raw'/run.id;destination.mkdir(exist_ok=False)
    run.command(['rsync','-r','--ignore-existing','--timeout=30','--contimeout=15',URL,str(destination)+'/'])
    allpaths=sorted(destination.rglob('*.jpg'));assert len(allpaths)==3013,len(allpaths)
    records=[]
    for p in allpaths:
        role='gallery' if p.parent.name=='database' else 'independent_query'
        meta=parse_name(p);assert meta['zone']=='56J' and meta['timestamp_field']==''
        with Image.open(p) as im:im.load();width,height=im.size
        records.append(dict(image_id='st_lucia:'+role+':'+p.name,role=role,relative_path=p.relative_to(ROOT).as_posix(),
            sha256=digest(p),width=width,height=height,**meta))
    records.sort(key=lambda r:(r['role'],r['traversal'],r['source_frame']))
    groups=collections.defaultdict(list)
    for r in records:groups[(r['role'],r['traversal'])].append(r)
    audit=[]
    for (role,traverse),r in groups.items():
        frames=np.array([x['source_frame'] for x in r]);assert len(np.unique(frames))==len(frames) and np.all(np.diff(frames)>0)
        coords=np.array([[x['easting'],x['northing']] for x in r]);steps=np.linalg.norm(np.diff(coords,axis=0),axis=1)
        audit.append(dict(role=role,traversal=traverse,images=len(r),source_frame_min=int(frames.min()),source_frame_max=int(frames.max()),
            source_frame_gap_min=int(np.diff(frames).min()),source_frame_gap_median=float(np.median(np.diff(frames))),
            source_frame_gap_max=int(np.diff(frames).max()),coordinate_step_median=float(np.median(steps)),coordinate_step_max=float(steps.max()),
            stationary_steps=int((steps==0).sum())))
    gallery=[r for r in records if r['role']=='gallery'];queries=[r for r in records if r['role']=='independent_query']
    assert len({r['traversal'] for r in gallery})==1,'Multiple gallery traversals require pre-freeze segmentation'
    gc=np.array([[r['easting'],r['northing']] for r in gallery]);qc=np.array([[r['easting'],r['northing']] for r in queries])
    distances=np.linalg.norm(qc[:,None]-gc[None],axis=2);gt={}
    for radius in [10,25,50]:
        valid=(distances<=radius).any(1);gt[str(radius)]=dict(total_queries=len(queries),with_positive=int(valid.sum()),without_positive=int((~valid).sum()),
            excluded_query_ids=[queries[i]['image_id'] for i in np.flatnonzero(~valid)])
    hashes=collections.defaultdict(list)
    for r in records:hashes[r['sha256']].append(r['image_id'])
    duplicates=[v for v in hashes.values() if len(v)>1]
    run.write('manifest.json',dict(dataset='St Lucia official formatted test-only subset',records=records))
    run.write('metrics.json',dict(role='metadata audit only; no retrieval performance',gallery_images=len(gallery),queries=len(queries),
        trajectories=audit,ground_truth_audit=gt,exact_duplicate_groups=duplicates,actual_bytes=sum(p.stat().st_size for p in destination.rglob('*') if p.is_file()),
        citation_and_permissions_readme=(destination/'README.txt').read_text(),image_redistribution=False,
        known_sampling_limit='Ordered source frame IDs retained, not uniformly sampled video. Velocity is index step, not physical speed. Gaps and geographic steps disclosed.'))
    run.write('checks.json',dict(passed=True,all_images_decoded_hashed=True,UTM_zone_consistent=True,strict_temporal_ID_order=True,
        one_gallery_traversal=True,no_reference_query_exact_byte_overlap=not any(any(':gallery:' in i for i in v) and any(':independent_query:' in i for i in v) for v in duplicates),
        new_independent_performance_unopened=True))
    (run.path/'per_query.csv').write_text('role,metadata_only\nindependent,true\n')
    (run.path/'interpretation.md').write_text('Coordinates define offline metric GT only. Online matcher gets cosine scores, never UTM, query IDs or filenames. Pano IDs recover source traversal and chronological order; timestamp field is empty. Curated irregular sampling limits index-velocity transfer; all audit gaps retained and no queries removed except disclosed no-positive closed-set exclusion and shared first-eight startup mask. Dataset photos are local only.\n')
    print(json.dumps(dict(run=run.id,gallery=len(gallery),queries=len(queries),trajectories=audit,GT={k:{a:b for a,b in v.items() if a!='excluded_query_ids'} for k,v in gt.items()})),flush=True)

if __name__=='__main__':main()
