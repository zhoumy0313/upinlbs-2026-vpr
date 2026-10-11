"""Independent closing audit; reads labels only OFFLINE and changes no science."""
import ast,bisect,csv,json,subprocess,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from runtime import ROOT,BASE,BRANCH,sha,write,preserve
from paper_tools import aliases
def read(p):return json.loads((ROOT/p).read_text())
def main():
    state=read('docs/goals/GOAL_V4_STATE.json');freeze=read(state['freeze_folder']+'/freeze.json');checks={}
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==BRANCH
    refs={'main':'78eb9e45d3bc469630b0c46ad1ea02b318ee151b','research/temporal-vpr-v2':'81fbf62dfaf5cdd28a005afbe6853289524b4d4d','research/vpr-v3-endpoint-refinement':BASE}
    for ref,h in refs.items():assert subprocess.check_output(['git','rev-parse',ref],cwd=ROOT,text=True).strip()==h,ref
    checks['old_files_preserved']=preserve();checks['old_branch_refs']=refs
    for p,h in freeze['file_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in freeze['raw_archives'].items():assert sha(ROOT/p)==h,p
    for model in freeze['model_identity'].values():
        source=model['source'];assert sha(ROOT/source['checkpoint'])==source['checkpoint_sha256']
        for p,h in model['source_python_sha256'].items():assert sha(ROOT/source['local_directory']/p)==h,p
    checks['freeze_and_actual_archives_models_verified']=True
    # A separate bisect implementation reconstructs every nearest-pose link.
    metadata=read('docs/research_v4/DATA_MANIFEST_r02.json');counts=[]
    for info in metadata['sequences']:
        rows=read(info['all_rgb_manifest']);raw=Path(info['extracted_root']);poses={}
        for line in (raw/'groundtruth.txt').read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):continue
            vals=list(map(float,line.split()));poses.setdefault(vals[0],vals[1:])
        times=sorted(poses);valid=0
        for r in rows:
            assert sha(ROOT/r['relative_path'])==r['sha256'],r['image_id']
            k=bisect.bisect_left(times,r['timestamp']);options=[x for x in [k-1,k] if 0<=x<len(times)]
            chosen=min(options,key=lambda x:(abs(times[x]-r['timestamp']),times[x]));t=times[chosen];delta=abs(t-r['timestamp'])
            assert t==r['gt_timestamp'] and delta==r['association_delta_seconds'] and (delta<=.03)==r['valid_gt']
            assert r['xyz']==(poses[t][:3] if r['valid_gt'] else None)
            assert r['quaternion_xyzw']==(poses[t][3:] if r['valid_gt'] else None);valid+=r['valid_gt']
        assert valid==info['valid_rgb_gt_matches'] and len(rows)-valid==info['invalid_rgb_gt_matches']
        counts.append(dict(sequence=info['sequence'],RGB=len(rows),valid=valid,invalid=len(rows)-valid))
    checks['all_image_hashes_and_independent_pose_links']=counts
    # No GT adapter/evaluator may be imported by online matching.
    tree=ast.parse((ROOT/'experiments/temporal_alignment_v4/algorithms.py').read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):assert not any(x in (node.module or '') for x in ['protocol','evaluation','groundtruth'])
        if isinstance(node,ast.Constant) and isinstance(node.value,str):assert node.value not in ['xyz','quaternion_xyzw','valid_gt','groundtruth']
    checks['online_interface_review']='scores, monotonic query clock, known gallery clocks/indices only; no label fields/imports'
    geometries={};metric_groups=0;row_count=0
    for field in ['g2_run','g3_run','g4_run']:
        folder=ROOT/'outputs_v4'/state[field];metrics=json.loads((folder/'raw_metrics.json').read_text())['results'];errors={}
        for m in metrics:
            key=m['sequence'],m['hz']
            if key in geometries:continue
            d=read(f'data/manifests/v4/{key[0]}_{key[1]}Hz_protocol.json')
            # The stored protocol has the actual gallery/query rows, no reconstruction choices.
            g=np.array([r['xyz'] for r in d['g']]);q=np.array([r['xyz'] if r['valid_gt'] else [np.nan]*3 for r in d['q']])
            geometries[key]=(d,np.linalg.norm(q[:,None,:]-g[None,:,:],axis=2))
        with (folder/'per_query.csv').open() as f:
            for row in csv.DictReader(f):
                key=row['sequence'],int(row['hz']);d,dist=geometries[key];i=int(row['query_index']);radius=float(row['radius_m']);p=json.loads(row['top10']);r=d['q'][i]
                assert r['image_id']==row['query_id'] and r['timestamp']==float(row['timestamp'])
                assert len(p)==10 and len(set(p))==10 and min(p)>=0 and max(p)<len(d['g'])
                valid=r['valid_gt'];positive=dist[i]<=radius;closed=bool(valid and positive.any());opened=bool(valid and not closed)
                assert int(row['valid_gt'])==valid and int(row['closed'])==closed and int(row['open'])==opened
                assert int(row['attempted'])==valid and int(row['rejected'])==0
                for k in [1,5,10]:assert int(row['hit'+str(k)])==bool(positive[p[:k]].any())
                if valid:assert abs(float(row['top1_distance_m'])-dist[i,p[0]])<1e-12
                c=json.loads(row['candidate_ids']);assert len(c)==int(row['candidate_count'])
                assert int(row['candidate_positive'])==bool(positive[c].any())
                mk=key+(row['method'],radius);errors.setdefault(mk,[]).append((valid,closed,float(row['top1_distance_m']) if valid else np.nan));row_count+=1
        for m in metrics:
            values=errors[m['sequence'],m['hz'],m['method'],m['radius_m']]
            a=np.array([x[2] for x in values if x[0]]);c=np.array([x[2] for x in values if x[1]])
            for scope,v in [('all_valid',a),('closed',c)]:
                for label,actual in [('median',np.median(v)),('P90',np.percentile(v,90))]:assert abs(m[f'top1_distance_{label}_{scope}']-actual)<1e-12
            metric_groups+=1
    checks['independent_geometry_and_error_audit']=dict(metric_groups=metric_groups,rows=row_count)
    replay=json.loads((ROOT/'outputs_v4/replay_full_stdout.log').read_text());assert replay['passed'] and replay['results'][-1]['passed'];assert not (ROOT/'outputs_v4/replay_full_stderr.log').stat().st_size
    checks['already_executed_cached_replay']=dict(passed=True,log_sha256=sha(ROOT/'outputs_v4/replay_full_stdout.log'),metric_groups=sum(x.get('metric_groups',0) for x in replay['results']),note='Already-seen deterministic replay, not another blind test')
    regression=ET.parse(ROOT/'outputs_v4/g4_freeze_20261011T033407Z_b4f7845e/all_regression.xml').getroot()
    suites=list(regression.iter('testsuite'));assert sum(int(x.attrib['tests']) for x in suites)==94 and all(int(x.attrib['errors'])==int(x.attrib['failures'])==0 for x in suites);checks['pre_freeze_regression']=94
    # Exact per-method rendered cells: accuracy, distances and measured latency.
    dev=read('docs/research_v4/BASELINE_RESULTS.json')['results']+read('configs/v4/selected_methods.json')['results'];test=read('docs/research_v4/INDEPENDENT_RESULTS.json')['results'];timing=read('docs/research_v4/REAL_TIMING_RESULTS.json');maps=read('paper/revisions/v4_r02/numeric_evidence_map.json');source=ROOT/'paper/revisions/v4_r02/main.tex';tex=source.read_text();assert sha(source)==maps['manuscript_sha256']
    for p,h in maps['sources'].items():assert sha(ROOT/p)==h
    exact_rows=[]
    for seq,metrics in [('freiburg2_pioneer_slam',dev),('freiburg3_long_office_household',test)]:
        for name,title in aliases():
            cells=[]
            for r in [.25,.5,1.]:
                m=next(x for x in metrics if x['method']==name and x['hz']==5 and x['radius_m']==r)
                cells.append('/'.join(f"{100*m['correct'+str(k)]/m['closed_queries']:.1f}" for k in [1,5,10]))
            m=next(x for x in metrics if x['method']==name and x['hz']==5 and x['radius_m']==.5)
            t=next(x for x in timing['results'] if x['sequence']==seq and x['method']==name)
            cells.extend([f"{m['top1_distance_median_all_valid']:.2f}/{m['top1_distance_P90_all_valid']:.2f}",f"{t['mean_ms']:.2f}/{t['P95_ms']:.2f}"])
            rendered=title+' & '+' & '.join(cells)+r' \\'
            assert rendered in tex,(seq,name);exact_rows.append(dict(sequence=seq,method=name,rendered=rendered))
    checks['paper_exact_rows']=exact_rows
    assert '38/2 RGB rows' in tex and '38/0 RGB rows' not in tex
    receipts=[]
    for version in ['v4_r01','v4_r02']:
        source=ROOT/'paper/revisions'/version/'main.tex';pdf=source.with_suffix('.pdf');matching=[]
        for p in (ROOT/'paper/revisions/v4_build_receipts').glob('*/receipt.json'):
            r=json.loads(p.read_text());v=r.get('versions',{}).get(version,{})
            if v.get('compiled') and v.get('source_sha256')==sha(source) and v.get('pdf_sha256')==sha(pdf):matching.append((p,v))
        assert matching,version+' requires exact-source export';p,v=matching[-1]
        assert v['pages']<=6 and v['all_fonts_embedded'] and not v['unresolved_references'] and not v['overfull_boxes']
        native=json.loads(source.with_name('native_compile_receipt.json').read_text());assert native.get('kind')=='success' or native.get('result',{}).get('kind')=='success'
        receipts.append(dict(version=version,receipt=str(p.relative_to(ROOT)),**v))
    checks['verified_manuscripts']=receipts
    figures=read('docs/research_v4/figures/figure_data.json')
    for name,coords in figures['sampling_coordinates'].items():
        for hz,pct in coords:
            m=next(x for x in dev if x['method']==name and x['hz']==hz and x['radius_m']==.5);assert abs(pct-100*m['R1'])<1e-12
    checks['figure_points_match_actual_metrics']=True
    assert state['first_independent_test_run']==state['g4_run'] and state['test_state']=='single_blind_run_complete'
    assert read('docs/research_v4/INDEPENDENT_RESULTS.json')['blind_evaluations']==1 and not state['positive_method_claim']
    checks['single_frozen_test_negative_gate']=True
    write(Path(sys.argv[1]),dict(passed=True,checks=checks));print(json.dumps(dict(passed=True,old_files=checks['old_files_preserved'],metric_groups=metric_groups,geometric_query_rows=row_count,pages=receipts[-1]['pages'])))
if __name__=='__main__':main()
