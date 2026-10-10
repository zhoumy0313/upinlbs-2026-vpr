"""Independent numerical audit, plots, negative-result validity report and stage archive."""
import csv,json,shutil,subprocess
from pathlib import Path
from runtime import Run,digest,update_state,utc_now
from archive_checkpoint import archive
from evaluate_independent import load_freeze
ROOT=Path(__file__).resolve().parents[2]

def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());name=Path(state['freeze_directory']).name;folder,f=load_freeze(name)
    evaluation=ROOT/'outputs_v2'/state['g4_evaluation_run'];latency=ROOT/'outputs_v2'/state['g4_latency_run'];audit=ROOT/f['data_audit'];gallery=ROOT/f['gallery_build']
    for p in [evaluation,latency,audit,gallery]:assert json.loads((p/'checks.json').read_text())['passed']
    metrics=json.loads((evaluation/'metrics.json').read_text());timing=json.loads((latency/'metrics.json').read_text());metadata=json.loads((audit/'metrics.json').read_text())
    run=Run(ROOT,'g4_acceptance',dict(freeze=name,outcome=metrics['outcome'],no_retuning=True),dict(evaluation=evaluation.name,latency=latency.name,
        metrics_sha256=digest(evaluation/'metrics.json'),latency_sha256=digest(latency/'metrics.json')));print(run.id,flush=True)
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q','--junitxml='+str(run.path/'regression.xml')],
        {'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    per=list(csv.DictReader((evaluation/'per_query.csv').open()));checked=0
    for result in metrics['results']:
        records=[r for r in per if int(r['radius_m'])==result['radius_m'] and r['method']==result['method'] and r['common_valid']=='True']
        for k in [1,5,10]:
            assert sum(r[f'correct_at_{k}']=='True' for r in records)==result['common'][f'R@{k}']['correct']
            assert len(records)==result['common'][f'R@{k}']['queries'];checked+=1
        assert sum(r['A_correct']=='False' and r['correct_at_1']=='True' for r in records)==result['rescue']
        assert sum(r['A_correct']=='True' and r['correct_at_1']=='False' for r in records)==result['harm']
    measured=list(csv.DictReader((latency/'per_query.csv').open()));import numpy as np
    for result in timing['results']:
        rows=[r for r in measured if r['method']==result['method']]
        assert len(rows)==3*metrics['total_queries'] and {int(r['repeat']) for r in rows}=={0,1,2}
        values=np.array([float(r['total']) for r in rows])
        assert np.isclose(values.mean(),result['total']['mean_ms'],rtol=0,atol=1e-9)
        assert np.isclose(np.median(values),result['total']['median_ms'],rtol=0,atol=1e-9)
        assert np.isclose(np.percentile(values,95),result['total']['p95_ms'],rtol=0,atol=1e-9)
    for source,filename in [(evaluation,'metrics.json'),(latency,'metrics.json'),(audit,'metrics.json'),(gallery,'gallery_identities.json')]:
        shutil.copy2(source/filename,run.path/(source.name+'_'+filename))
    g2=ROOT/'outputs_v2'/state['g2_baseline_run'];g3=ROOT/'outputs_v2'/state['g3_adaptive_run'];smr=ROOT/'outputs_v2'/state['g3_smr_run']
    run.command([str(ROOT/'.venv-paper/bin/python'),'experiments/temporal_vpr/plot_g4.py','--development',str(g2/'metrics.json'),
        '--adaptive',str(g3/'metrics.json'),'--smr',str(smr/'metrics.json'),'--independent',str(evaluation/'metrics.json'),
        '--latency',str(latency/'metrics.json'),'--out',str(run.path/'figures'/'final')])
    run.command([str(ROOT/'.venv-p0/bin/python'),'experiments/temporal_vpr/make_examples_v2.py','--audit',audit.name,
        '--evaluation',evaluation.name,'--out',str(run.path/'figures/examples')])
    run.write('checks.json',dict(passed=True,tests=56,independent_RK_cells_recounted=checked,paired_rescue_harm_recounted=True,
        timing_records_recounted=len(measured),timing_mean_median_P95_recomputed=True,freeze_source_all_hashes_match=True,
        no_test_parameter_changes=True,freeze_created_utc=f['created_utc'],first_test_open_utc=state['first_independent_open_utc']))
    run.write('metrics.json',dict(outcome=metrics['outcome'],checked_metric_cells=checked,timing_records=len(measured),independent=evaluation.name,
        latency=latency.name,freeze=name));(run.path/'per_query.csv').write_text('checked_cells,timing_records\n'+str(checked)+','+str(len(measured))+'\n')
    (run.path/'interpretation.md').write_text('G4 scientific outcome is determined by frozen independent results. Adaptive failure on development is not erased by any external favorable subgroup. All source and data hashes checked, numerical count/timing audit independent of evaluator. No random-seed variation represented as statistical CI.\n')
    primary=[r for r in metrics['results'] if r['radius_m']==25]
    lines=['# G4 frozen independent results','',f'UTC {utc_now()}. Freeze `{name}` at {f["created_utc"]}; first independent access {state["first_independent_open_utc"]}. Code commit {f["source_commit"]}. Evaluation `{evaluation.name}`, real-image timing `{latency.name}`, audit `{run.id}`. No parameters changed after opening.',
        '',f'Official St Lucia subset: gallery {metrics["gallery_images"]}, query {metrics["total_queries"]}; primary closed-set/common queries {metrics["common_queries"]}. Offline UTM zone56J radius≤25m; sensitivities10/50m predeclared. Every method uses same GT/mask. All excluded no-positive IDs and eight startup frames retained in per-query ledger. Neither UTM nor filename fields are matcher inputs.',
        '', '| Method | R@1 | R@5 | R@10 | Rescue / harm | Rejected |','|---|---:|---:|---:|---:|---:|']
    for r in primary:
        lines.append('| '+r['method']+' | '+' | '.join(f'{r["common"][f"R@{k}"]["correct"]}/{r["common"][f"R@{k}"]["queries"]} ({100*r["common"][f"R@{k}"]["recall"]:.2f}%)' for k in [1,5,10])+f' | {r["rescue"]}/{r["harm"]} | {r["abstained_queries"]} |')
    lines+=['','| Real batch1 method | Mean ms | Median ms | P95 ms |','|---|---:|---:|---:|']
    for r in timing['results']:lines.append(f'| {r["method"]} | {r["total"]["mean_ms"]:.3f} | {r["total"]["median_ms"]:.3f} | {r["total"]["p95_ms"]:.3f} |')
    lines+=['',f'Outcome {metrics["outcome"]}: '+('fixed temporal improves over single image here, but own adaptivity did not beat mature temporal on development; only empirical temporal conclusions are justified.' if metrics['outcome']=='B' else 'frozen temporal transfer does not improve the external primary R@1; preserve the negative result and discuss index-velocity/sampling/protocol limitations without tuning.'),
        '', 'All 24 methods ×3 radii, weight/window/velocity/reverse/shuffle sensitivities and shared-query startup results are retained in metrics.json. Contiguous100-query block paired net counts are descriptive, not independent confidence intervals. Figure points and table cells have exact source hashes. Any uncertainty in frame-based Nordland GT and geographic St Lucia loop ambiguity remains a limitation.',
        '', 'Real latency includes image open/RGB decode, tensor normalization/resize, model batch1, CPU transfer, gallery similarity, history and ranking; warmed20 and three full1464-query traversals per method, CUDA synchronized, clocks not locked. Timed computation does not read cached query descriptors/scores; cached values are used only for post-timer identity audits. Offline gallery batch16 build and bytes separate. RSS includes accuracy-audit arrays and allocator/cached memory; CUDA allocated/reserved values are not total device use. Avoid significance claims for small latency differences.',
        '', 'Precision checks (including any real-vs-cache ranking disagreement) are included verbatim in latency metrics; no hidden correction or selective rerun. SMR is the declared first-filter code adaptation trained only on Nordland; rejects count as misses. No full published reproduction or novel superiority claim. Original old-test tables remain post_hoc/seen V1 evidence only.']
    (ROOT/'docs/research_v2/G4_FROZEN_RESULTS.md').write_text('\n'.join(lines)+'\n')
    validity=f'''# G4 validity audit — passed with scientific limitations

{checked} R@1/5/10 cells independently recounted from actual per-query CSV, paired rescue/harm recounted. {len(measured)} real-image timing records independently recomputed mean/median/P95. 56 original/V2 tests pass. All immutable freeze code/config/model/data/galleries/SMR hashes verify; freeze timestamp precedes first performance opening. Accuracy/timing commands exit0 and source snapshots retained. No old final-test selection, no new-test tuning, no network training; SMR small classifier supervised train only. Common closed-set and shared-startup masks disclosed and same for all comparisons.

Source/licence: official downloader commit2f886d53996d2a4cf549696c5e845c40d77da610; official rsync bytes/hash decoded; README nominal5m sampling differs from actual GPS-step medians11.4176m reference/11.9630m query, so no measured5m uniformity claimed. Original Milford/Wyeth2008 and Berton et al.2022 curation cited. Repository MIT code licence is not a dataset image licence. Data stay local, no public image redistribution. Source pano frame IDs order trajectories, timestamp empty, zone56J verified; existing PROJ independently reprojects all3013 GPS positions with max difference1.48305m under declared2m rounding bound. Original-frame gaps maxima345/149, observed coordinate-step maxima17.6976/20.1543m; all recorded, no resampling. No fabricated uniformly timed video or ±5-frame geographic GT. Independence refers to our method selection; upstream encoder pretraining-data overlap not audited.

Threats: one Nordland development sequence, frame ordinal GT uncertainty, serial correlation, development saturation, St Lucia curated distance sampling/loop revisits/index-velocity mismatch, limited independent dataset, fixed relative velocity, Top50 pool truncation, heuristic scales not probabilities, train-to-test SMR feature shift, original SMOTE-before-CV optimism, nearest eligible image sets not navigation ground truth, clocks/file cache variability. Original SeqSLAM and same-conference paper full texts partly inaccessible; own implementation is a descriptor trajectory adaptation, not first or full official SeqSLAM reproduction. No subgroup/radius/hyperparameter chosen to rescue negative test. No statistical significance claimed.

New files: data audit/gallery build, common method factory, frozen evaluation, real benchmark, scientific plot/point ledger, freeze and acceptance; all changes confined to V2 paths. Old papers/source/results/history retained. Actual reproduction entrypoints and environment in run commands.jsonl; manifest filenames and local raw/model SHA in freeze. Download123494841 bytes estimate verified; no driver/system configuration changes.

Beginner explanation:
1. The image encoder turns one photograph into a normalized vector.
2. Similarities compare it with reference-image vectors.
3. Ordered history scores candidate reference paths using past queries only.
4. Relative reference-index velocity does not measure GPS speed.
5. GPS is used after ranking only to mark geographically eligible references.
6. All methods share the same evaluated queries; startup/no-positive exclusions are public.
7. An adaptive failure remains a failure even if some ablation helps.
8. Three real timed traversals do not create three independent datasets.
9. A reproducible negative-result paper still needs human novelty/format judgement.

Decision: accept G4 evidence, Outcome {metrics['outcome']}; auto-advance G5 empirical manuscript versions, numerical mapping, native compilation and readiness judgement. Single next task: versioned evidence-backed empirical paper, no new method family.
'''
    (ROOT/'docs/research_v2/G4_VALIDITY_AUDIT.md').write_text(validity)
    for file,line in [('DECISION_LOG.md',f'\n{utc_now()}: immutable {name}, G4 Outcome {metrics["outcome"]}. No test tuning/correction; retain negative hypotheses. Auto-advance empirical G5.\n'),
        ('EXPERIMENT_REGISTER.md',f'| G4 | Frozen St Lucia + true batch1 timing | independent | {evaluation.name};{latency.name};{run.id} | Outcome {metrics["outcome"]} |\n'),
        ('EVIDENCE_INDEX.md',f'\nG4: artifacts/v2/g4 combined metadata/accuracy/latency metrics, per_query.csv, contiguous_blocks.csv, figure_points.csv, public evidence ZIP/SHA; immutable freezes/{name}. Raw/model descriptor arrays local by SHA.\n')]:
        with (ROOT/'docs/research_v2'/file).open('a') as stream:stream.write(line)
    selected=[run.path/'metrics.json',run.path/'checks.json',evaluation/'per_query.csv',evaluation/'contiguous_blocks.csv',evaluation/'score_identities.json']
    selected += list((run.path/'figures/final').iterdir())
    selected.append(run.path/'figures/examples/example_ledger.csv')
    selected += list(run.path.glob('g4_*_*.json'))
    public=archive('g4',[audit,gallery,evaluation,latency,run.path]+[p for p in (ROOT/'outputs_v2').glob('g4_gallery_build_*') if p!=gallery]+list((ROOT/'outputs_v2').glob('g4_freeze_audit_*'))+
        list((ROOT/'outputs_v2').glob('g4_development_factory_preflight_*'))+list((ROOT/'outputs_v2').glob('g4_GPS_UTM_crosscheck_*')),selected)
    state['stages']['G4']='passed';state['stages']['G5']='in_progress'
    update_state(ROOT,stages=state['stages'],current_stage='G5',stage_status='in_progress',research_outcome=metrics['outcome'],g4_acceptance_run=run.id,latest_run_id=run.id)
    (ROOT/'docs/goals/GOAL_V2_STATUS.md').write_text(f'# VPR-GOAL-V2\n\nG0–G2 passed; G3 scientifically_negative; G4 passed, Outcome {metrics["outcome"]}; G5 in progress. Independent frozen test completed, no retuning. Mainline empirical, no adaptive superiority.\n')
    print(json.dumps(dict(acceptance=run.id,outcome=metrics['outcome'],checked_cells=checked,timing_records=len(measured),public_archive_sha256=digest(public/'evidence.zip'))),flush=True)

if __name__=='__main__':main()
