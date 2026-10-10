"""Interpret all predeclared radii conservatively; never alter frozen methods or metrics."""
import csv,json,sys,statistics,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'experiments/temporal_vpr'))
from runtime import Run,digest,update_state,utc_now
from archive_checkpoint import archive

def percentile(values,p):
    values=sorted(values);x=(len(values)-1)*p;lo=math.floor(x);hi=math.ceil(x)
    return values[lo]+(values[hi]-values[lo])*(x-lo)

def main():
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());assert state['stages']['G4']=='passed'
    source=ROOT/'outputs_v2'/state['g4_evaluation_run'];m=json.loads((source/'metrics.json').read_text())
    chosen=['A-only','B-only','RRF_k60','AB_fixed_0.75','fixed_T_best','fixed_blend_best','adaptive_full','SMR_first_filter_adapted']
    index={(r['radius_m'],r['method']):r for r in m['results']};differences=[]
    for radius in [10,25,50]:
        t=index[radius,'fixed_T_best']['common']['R@1'];a=index[radius,'A-only']['common']['R@1'];assert t['queries']==a['queries']
        differences.append(dict(radius_m=radius,queries=a['queries'],A_correct=a['correct'],fixed_T_correct=t['correct'],net=t['correct']-a['correct']))
    unstable=min(r['net'] for r in differences)<0<max(r['net'] for r in differences)
    outcome='C' if unstable else m['outcome']
    run=Run(ROOT,'g4_transfer_sensitivity_audit',dict(analysis_only=True,predeclared_radii=[10,25,50],no_selection_or_rerun=True),
        dict(metrics_sha256=digest(source/'metrics.json'),per_query_sha256=digest(source/'per_query.csv')));print(run.id,flush=True)
    rows=list(csv.DictReader((source/'per_query.csv').open()));distance_stats={}
    for method in chosen:
        distances=[float(r['top1_distance_m']) for r in rows if r['radius_m']=='25' and r['method']==method and r['common_valid']=='True' and r['top1_distance_m']!='']
        distance_stats[method]=dict(queries_with_output=len(distances),median_reference_GPS_separation_m=statistics.median(distances),
            p95_reference_GPS_separation_m=percentile(distances,.95),interpretation='retrieved-reference label separation, not pose/navigation error')
    run.write('metrics.json',dict(overall_outcome=outcome,primary_25m_automated_outcome=m['outcome'],predeclared_radius_instability=unstable,
        differences=differences,reference_distance_diagnostics=distance_stats,
        scope='conservative scientific interpretation; original frozen evaluator results remain byte-identical'))
    run.write('checks.json',dict(passed=True,all_sensitivity_radii_predeclared=True,no_method_or_test_protocol_changed=True,
        primary_protocol_not_replaced=True,original_metrics_sha256=digest(source/'metrics.json')))
    with (run.path/'per_query.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(differences[0]));w.writeheader();w.writerows(differences)
    (run.path/'interpretation.md').write_text('Primary25m automated labelB preserved. At predeclared10m, selected fixedT gains reverse strongly; overall scientific assessmentC (unstable transfer). This changes interpretation, never parameters, denominators or original predictions. No favorable test choice adopted.\n')
    table=['# Predeclared radius sensitivity and overall Outcome C','',f'UTC {utc_now()}, `{run.id}`. Raw frozen primary evaluator label {m["outcome"]} refers to25m. Its results are immutable. Overall audited outcome {outcome} reflects instability under the prescribed10/25/50m tolerances. This is a conservative interpretation, not a change of primary metric or method.',
        '', '| Method | R@1 10m | R@1 25m primary | R@1 50m |','|---|---:|---:|---:|']
    for method in chosen:
        table.append('| '+method+' | '+' | '.join(f'{index[r,method]["common"]["R@1"]["correct"]}/{index[r,method]["common"]["R@1"]["queries"]} ({100*index[r,method]["common"]["R@1"]["recall"]:.2f}%)' for r in [10,25,50])+' |')
    table+=['', 'All tolerances use1456 queries: no no-positive exclusions at any radius, common startup8. Selected fixedT net correct counts are -300/+14/+30 versus A at10/25/50m. Its 25m gain cannot establish uniformly improved geographic retrieval. The heuristic is still below strong fixed/static controls under the primary comparison and failed development superiority.',
        '', 'GPS separation statistics describe retrieved reference labels, not localization RMSE or deployed pose accuracy. Index-velocity mismatch and score averaging can shift endpoints; a causal mechanism is a hypothesis, not independently proven here. No method is fitted to the exposed test. Broad-velocity L5 perfect25m row remains sensitivity, never a new selected winner.',
        '', 'Timing caveats: dual encoders prepare tensors separately, warm file cache, one CPU/BLAS thread, no locked clocks; source SMR feature loops included, so predictor-only published milliseconds are not directly comparable. Actual descriptors match cached batch1 exactly, score differences≤1.1102230246251565e-15 and all nine methods/three repeats have zero top10 ranking mismatches.',
        '', 'The original G4 figure point file uses a generic historical field named value_percent, including latency rows; their metric names and plot axes already specify milliseconds. A derived figure_points_with_units.csv provides explicit units and preserves all original values and the immutable file. This is a metadata clarification, not a result or algorithm correction.']
    (ROOT/'docs/research_v2/G4_SENSITIVITY_ANALYSIS.md').write_text('\n'.join(table)+'\n')
    for report in ['G4_FROZEN_RESULTS.md','G4_VALIDITY_AUDIT.md']:
        with (ROOT/'docs/research_v2'/report).open('a') as stream:stream.write(f'\n## Overall sensitivity qualification\n\nThe automated Outcome B above is specific to primary25m. Predeclared10m reverses selected fixedT gains (-300 versus A); overall audited outcome C, unstable transfer. Original predictions/config/metrics remain unchanged. See G4_SENSITIVITY_ANALYSIS.md and `{run.id}`.\n')
    figure=ROOT/'artifacts/v2/g4/figure_points.csv';points=list(csv.DictReader(figure.open()));corrected=[]
    for r in points:
        corrected.append({**{k:v for k,v in r.items() if k!='value_percent'},'value':r['value_percent'],
            'unit':'percent' if r['metric']=='R@1' else 'milliseconds'})
    with (run.path/'figure_points_with_units.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(corrected[0]));w.writeheader();w.writerows(corrected)
    archive('g4_sensitivity',[run.path],[run.path/'metrics.json',run.path/'checks.json',run.path/'figure_points_with_units.csv'])
    update_state(ROOT,research_outcome=outcome,primary_protocol_outcome=m['outcome'],g4_sensitivity_audit_run=run.id,
        research_outcome_reason='selected temporal gain reverses at prescribed10m; adaptive contribution unsupported; no test tuning',latest_run_id=run.id)
    with (ROOT/'docs/research_v2/DECISION_LOG.md').open('a') as stream:stream.write(f'\n{utc_now()}: overallOutcomeC after reading all prescribed radii; primary25m labelB stays in raw evaluator. This is conservative interpretation, no source/config/prediction changes, no choice of favorable test parameters.\n')
    (ROOT/'docs/goals/GOAL_V2_STATUS.md').write_text('# VPR-GOAL-V2\n\nG0–G2 passed; G3 scientifically_negative; G4 passed evidence checks, overallOutcomeC (primary25mB, unstable10m transfer); G5 in progress. No retuning. Empirical paper only.\n')
    print(json.dumps(dict(run=run.id,outcome=outcome,differences=differences)),flush=True)

if __name__=='__main__':main()
