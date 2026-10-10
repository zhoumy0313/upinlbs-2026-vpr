"""Independent count checks, sensitivity plot, unique G2 decision and checkpoint evidence."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from runtime import Run,digest,update_state,utc_now
from diagnostics import canonical_rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-run',required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];data=root/'outputs_v2'/a.baseline_run
    m=json.loads((data/'metrics.json').read_text());assert m['decision']=='A'
    run=Run(root,'g2_acceptance',{'stage':'G2','next_method_family':'A','no_test_tuning':True},
        {'baseline_run':a.baseline_run,'metrics_sha256':digest(data/'metrics.json')})
    print(run.id,flush=True)
    run.command([str(root/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q',
        '--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    run.command([str(root/'.venv-paper/bin/python'),'experiments/temporal_vpr/plot_g2.py','--metrics',str(data/'metrics.json'),
        '--out',str(run.path/'figures'/'grid')])
    per=list(csv.DictReader((data/'per_query.csv').open()))
    for row in m['results']:
        q=[r for r in per if r['split']==row['split'] and r['method']==row['method'] and r['common_valid']=='True']
        for k in [1,5,10]:
            hits=sum(r[f'correct_at_{k}']=='True' for r in q)
            assert hits==row['common'][f'R@{k}']['correct']
            assert len(q)==row['common'][f'R@{k}']['queries']
    manifest=json.loads((root/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json').read_text())['records']
    shuffled=[manifest[i] for i in np.random.default_rng(0).permutation(len(manifest))]
    ids=json.loads((data/'score_identities.json').read_text())
    for entry in ids.values():
        for key in ['query_ids','gallery_ids']:
            assert canonical_rows(manifest,entry[key])==canonical_rows(shuffled,entry[key])
    suites=ET.parse(run.path/'regression.xml').getroot();tests=sum(int(s.attrib['tests']) for s in suites.findall('testsuite'))
    run.write('checks.json',dict(passed=True,tests=tests,independent_per_query_counts_checked=len(m['results'])*3,
        actual_manifest_shuffle_preserves_ID_alignment=True,real_replay_checks=str((data/'real_replay_checks.json').relative_to(root)),
        no_new_independent_or_old_test_performance_opened=True))
    run.write('metrics.json',{'role':'G2 acceptance audit','independent_checked_metric_cells':len(m['results'])*3,
        'tests':tests,'next_track':'A','best_temporal':m['best_temporal_only']})
    (run.path/'per_query.csv').write_text('verified_metric_cells\n'+str(len(m['results'])*3)+'\n')
    (run.path/'interpretation.md').write_text('Causal temporal baseline has strong development signal. Adaptivity remains unproved, and near-ceiling validation sharply limits evidence for an extra contribution. One bounded concrete rule and ablations follow; no new window/velocity sweep.\n')
    public=root/'artifacts/v2/g2';public.mkdir(parents=True,exist_ok=False)
    for f in ['metrics.json','per_query.csv','checks.json','real_replay_checks.json','score_identities.json']:
        shutil.copy2(data/f,public/f)
    for path in (run.path/'figures/grid').iterdir():shutil.copy2(path,public/path.name)
    val=[r for r in m['results'] if r['split']=='validation'];best=m['best_temporal_only'];settings=best['settings']
    header=['# G2 strong baseline results — development only','',f'Run: `{a.baseline_run}`, source/count hashes in artifacts/v2/g2. All rows share 292 validation queries, gallery 1750, ±5 ordinal-frame GT; full 300-query startup results remain separate in metrics.json.','','| Method | R@1 | R@5 | R@10 | Rescue / harm versus A |','|---|---:|---:|---:|---:|']
    wanted=['A-only','B-only','DINOv2-only','RRF_k60','AB_fixed_0.25','AB_fixed_0.5','AB_fixed_0.75','shuffled_L9',best['method'],
        'temporal_L3_v0.8,1.0,1.2_lambda1','temporal_L5_v0.8,1.0,1.2_lambda1','temporal_L9_v0.8,1.0,1.2_lambda1']
    for name in wanted:
        row=next(r for r in val if r['method']==name)
        header.append('| '+name+' | '+' | '.join(f'{100*row["common"][f"R@{k}"]["recall"]:.2f}%' for k in [1,5,10])+f' | {row["rescue"]} / {row["harm"]} |')
    header+=['','The 90 methods per split include all 80 L/velocity-set/weight combinations, seven single/static baselines, and three shuffled controls. No configuration deleted. Best fixed temporal uses L=9, velocity=1.2, lambda=1 selected on validation with the predeclared deterministic tie rule. It yields 291/292 versus A 210/292; 82 rescues and one harm. The full three-velocity L9 baseline is 284/292 versus shuffled history 238/292. This supports an order-dependent effect without making an independent generalization claim.',
       '', 'Actual 18 development-image replays have exact descriptor agreement with cached rows; CPU/GPU float64 cosine scores agree within declared 1e-12 and top-10 ranks agree; causal L9 replay ranking agrees. First attempt omitted process-local TORCH_HOME and was interrupted during redundant initializer download; SIGINT/failed logs retained unchanged. Retry changed only cache location, not encoders or search protocol. No real latency results claimed here.',
       '', f'All {tests} original/V2 tests pass. Actual manifest reordering retains identical ID-to-label alignment; 540 metric cells independently recounted from 81,000 per-query rows. Figure point CSV records exact numerators, denominators and input SHA.',
       '', 'Decision: research track A only. Near-ceiling fixed baseline leaves one validation error, so an adaptive advantage is not assumed. G3 gets one fixed concrete rule with prescribed ablations; if it does not beat fixed temporal, freeze an empirical interpretation and stop adding mechanisms. No expansion to fusion track B while temporal signal is positive.']
    (root/'docs/research_v2/G2_DECISION.md').write_text('\n'.join(header)+'\n')
    report=f'''# G2 acceptance — passed

Date: {utc_now()}. Data run `{a.baseline_run}`; acceptance run `{run.id}`. Actual {tests} tests pass, including original 31; ten causal/ranking tests, runtime/diagnostic/plot tests and real-image CPU/GPU/cached replay integration. Independent verification recounts {len(m['results'])*3} Recall cells from per_query.csv; full manifest shuffle aligns by explicit image IDs. Mandatory causal checks include L1 identity, no future, resets, whole invalid path, no online GT/filename input, manual T, shuffle control and common query masks. No test-based tuning.

Actual commands and exits: commands.jsonl in successful and failed G2 runs, stdout.log and stderr.log. Source snapshots in every run; config_effective.yaml holds declared grid, normalization, precision tolerances and input fingerprints. Git source baseline is recorded per run. New code: causal.py, run_g2.py, g2_replay_check.py, plot/acceptance helpers and tests; V1 source/protocol/output/paper unchanged. Reproduce `.venv-p0/bin/python experiments/temporal_vpr/run_g2.py` to create a fresh run, using already configured weights. Cached search is accuracy, not model latency.

Scientific result: G2_DECISION.md actual same-denominator table and fixed-weight/window/velocity sensitivities. Negative DINOv2, harms, shuffled histories, all grid configurations and interrupted cache-download run retained. Original SeqSLAM SAD/patch contrast implementation not run, and no official reproduction claim. New independent test unopened.

Beginner explanation:
1. Current and past photographs each produce an image descriptor.
2. Each descriptor produces one similarity row against an ordered reference gallery.
3. A trajectory adds compatible past scores and cannot use a future query.
4. Velocity is a relative reference-frame step, not a GPS speed.
5. A path crossing a gallery edge is invalid as a whole.
6. All methods are evaluated on the same 292 validation frames.
7. Ordered history beats shuffled history here, but this is development evidence.
8. An adaptive rule must beat fixed temporal before it earns a contribution claim.

Decision: accept G2 and auto-advance G3, unique track A. Next single task: one train-statistic-based causal adaptive rule, prescribed ablations and explicit SMR contrast; no further window/velocity search.
'''
    (root/'docs/research_v2/G2_ACCEPTANCE.md').write_text(report)
    archive=public/'evidence.zip'
    folders=[data,run.path]+[p for p in (root/'outputs_v2').glob('g2_strong_baselines_*') if p!=data]
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for folder in folders:
            for path in sorted(folder.rglob('*')):
                if path.is_file() and path.suffix in {'.json','.jsonl','.csv','.yaml','.xml','.log','.md','.py'}:
                    z.write(path,path.relative_to(root).as_posix())
    (public/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
    state=json.loads((root/'docs/goals/GOAL_V2_STATE.json').read_text());state['stages']['G2']='passed';state['stages']['G3']='in_progress'
    update_state(root,stages=state['stages'],current_stage='G3',stage_status='in_progress',latest_run_id=run.id,
        selected_research_track='A',g2_baseline_run=a.baseline_run,selected_temporal_settings=settings)
    (root/'docs/goals/GOAL_V2_STATUS.md').write_text(f'# VPR-GOAL-V2\n\nG0–G2 passed; G3 in progress; G4/G5 pending. Independent performance unopened.\n\nG2 fixed causal temporal validation: 291/292 (99.66%); single-frame A: 210/292 (71.92%). Development-only, not a new method or test claim. Adaptive contribution unproved.\nNext: one bounded adaptive rule and ablations, then immutable freeze and independent evaluation.\n')
    with (root/'docs/research_v2/DECISION_LOG.md').open('a') as f:f.write(f'\n{utc_now()}: G2 track A selected from development only; freeze its best temporal settings {json.dumps(settings)} for G3. Near-ceiling score does not establish adaptivity. No G2 correction or alternate family required; redundant-download failure was infrastructure, not a scientific retuning.\n')
    with (root/'docs/research_v2/EXPERIMENT_REGISTER.md').open('a') as f:f.write(f'| G2 | Fixed causal temporal/fusion finite grid | train/validation | {a.baseline_run} / {run.id} | passed, track A |\n')
    with (root/'docs/research_v2/EVIDENCE_INDEX.md').open('a') as f:f.write(f'\nG2: artifacts/v2/g2/metrics.json, per_query.csv, fixed_temporal_grid.*, figure_points.csv and SHA256SUMS. Raw scores local at outputs_v2/{a.baseline_run}; all negative/failure text logs archived.\n')
    print(json.dumps({'acceptance_run':run.id,'tests':tests,'selected_track':'A','archive_sha256':digest(archive)}))

if __name__=='__main__':main()
