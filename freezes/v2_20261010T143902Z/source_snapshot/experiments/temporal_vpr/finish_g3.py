"""Accept a disproved hypothesis honestly; stop method additions and advance G4."""
import csv,json,shutil
from pathlib import Path
from runtime import Run,digest,update_state,utc_now
from archive_checkpoint import archive
ROOT=Path(__file__).resolve().parents[2]

def main():
    adaptive=ROOT/'outputs_v2/g3_adaptive_development_20261010T134356Z_93dbfee7'
    smr=ROOT/'outputs_v2/g3_smr_adaptation_20261010T135720Z_bcbbf327'
    a=json.loads((adaptive/'metrics.json').read_text());s=json.loads((smr/'metrics.json').read_text())
    assert not a['adaptive_exceeds_strongest_fixed']
    run=Run(ROOT,'g3_acceptance',dict(scientific_status='scientifically_negative',final_track='A_empirical',no_more_modules=True),
        dict(adaptive_metrics_sha256=digest(adaptive/'metrics.json'),smr_metrics_sha256=digest(smr/'metrics.json')))
    print(run.id,flush=True)
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','-q',
        '--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    checked=0
    for folder,metrics in [(adaptive,a),(smr,s)]:
        rows=list(csv.DictReader((folder/'per_query.csv').open()))
        for r in metrics['results']:
            per=[p for p in rows if p['split']==r['split'] and p['method']==r['method'] and p['common_valid']=='True']
            for k in [1,5,10]:
                assert sum(p[f'correct_at_{k}']=='True' for p in per)==r['common'][f'R@{k}']['correct']
                assert len(per)==r['common'][f'R@{k}']['queries'];checked+=1
    result=dict(scientific_status='scientifically_negative',implementation_verified=True,checked_cells=checked,
        own_rule_not_superior=True,adaptive_results=a,SMR_adaptation_results=s)
    run.write('metrics.json',result);run.write('checks.json',dict(passed=True,tests=53,negative_conclusion_supported=True,
        no_independent_performance_opened=True,independent_recount_cells=checked))
    (run.path/'per_query.csv').write_text('checked_metric_cells\n'+str(checked)+'\n')
    (run.path/'interpretation.md').write_text('Stage artifacts accepted; scientific adaptive hypothesis rejected on development. This is not a positive-method acceptance. Stop additions, freeze empirical comparison, test transfer once.\n')
    docs=ROOT/'docs/research_v2'
    method='''# METHOD V2 — frozen empirical track A

## Problem and contribution boundary
Single-frame retrieval can misrank visually similar locations. Existing sequence matching, descriptor temporal aggregation, confidence filtering and candidate reranking precede this work. We test a bounded causal implementation and one heuristic; we do not claim first sequence matching or a new network. The adaptive contribution is disproved on development and will not be tuned on new independent data. Final paper mainline: an empirical audit of temporal gain, transfer and adaptive failure.

## Inputs, scores and causal trajectory
A fixed image encoder maps an RGB image, full-frame tensor resize 224×224 after ImageNet normalization, into an L2-normalized descriptor (CosPlace R18/512, EigenPlaces R50/512, DINOv2 ViT-S/14 CLS/384). Similarity is float64 unit-renormalized cosine clipped to [-1,1]. Only ordered gallery index and current/past score rows enter a matcher. Filenames, query order IDs, GPS and GT are unavailable to its score-only API. Offline GT labels never enter a trajectory or adaptive weight.

For endpoint j: T_t(j)=max_{v in V} (1/L) sum_{lag=0}^{L-1} S_{t-lag}(j-rint(v*lag)). Round uses NumPy ties-to-even. A whole path is invalid (-Inf) if any reference index is out of range. Stable descending ties retain gallery order. Reset at each traversal/split, retain at most L score rows. First L-1 queries use A. All principal comparisons exclude first 8 queries per traversal, including single-frame methods; full-stream startup is reported separately.

Known-range normalization f(x)=(x+1)/2; blend=(1-lambda)f(S)+lambda f(T), invalid paths remain -Inf for lambda>0, lambda=0 is exact A. No whole-query-matrix/test fitting. G2 selected L=9,V={1.2},lambda=1 using only development validation. The predeclared grid included L={1,3,5,9}, V={0.8},{1.0},{1.2},{0.8,1.0,1.2}, lambda={0,.25,.5,.75,1}; all 80 grid and ten controls per split retained. RRF uses full-gallery ranks 1-based, sum 1/(60+rank), no learned coefficient.

## One predeclared adaptive rule and all ablations
Current A Top-50 candidates C_t are reranked with the same L=9,V={1.2}; the A tail is unchanged. Define g_A,g_T as largest minus second-largest finite score. Train-only medians are m_A=0.021545156781904273 and m_T=0.018370866637548056 over 592 valid training queries, without GT. Values floor at epsilon=1e-12. Ambiguity a=clip(1-g_A/m_A,0,1); support b=clip(g_T/m_T,0,1). Full-gallery T endpoint argmax is recorded before current reranking. Continuity c is the mean of up to two past endpoint increments within absolute tolerance 1 of median(V); first valid endpoint uses c=1. Candidate agreement d=1 if T endpoint is in current Top50, otherwise .25. Weight lambda_t=a*b*c*d. These constants were declared before G3; no coefficients were optimized. No valid candidate path falls back to A. Ablations remove c, remove a, remove d; controls replace weight by the development-selected interior fixed weight .75 or .5 or 1 on the identical Top50 pool. Full-gallery best fixed temporal remains the strongest mandatory comparator.

The adaptive rule achieves 242/292 validation R@1, below full fixed temporal 291/292 and fixed Top50 temporal 287/292. Removing ambiguity gives 261/292, removing continuity 248/292, removing agreement 244/292; no further module or hyperparameter additions are allowed. This evidence cannot support an adaptive superiority claim.

## SMR source and protocol differences
SMR IROS 2025 source: Somayeh Hussaini, Tobias Fischer and Michael Milford, github.com/SoftwareImpacts/S... [exact repository URL in predeclaration/source receipt], commit 82c88c90377110ce7a3340872f3e1179c3f2d396, MIT license. Selected original function AST bodies are executed unchanged; origin source commit/clean state is checked. Original license stays in third_party. Training callbacks save diagnostics rather than plots, without changing fitting.

First-filter adaptation uses its four original ratio features, topN=1, epsilon=1e-6, group window2, L9 unit-velocity diagonal convolution, original four supervised classes, StandardScaler and 3×128 MLP, source-code defaults alpha=.0001/lr=.001/random_state0, SMOTE random_state42 and five-fold single-config GridSearch. Original CV occurs after SMOTE and is optimistic: it is never treated as independent evidence. Train data only: 592 windows from Nordland 600 queries versus gallery1750, ±5 ordinal GT; the paper used multiple descriptors/square geographies and different GT/hyperparameters. We use frozen CosPlace, not all published models. GPU networks are never trained. Confidence cutoff0 represents original all-trusted operating point and avoids future-dependent full-test quantiles. Class1/3 rejection counts as misses in all-query R@K. Restoration is not implemented. Transfer uses the Nordland-trained classifier without independent-dataset retraining. Therefore this is a related-code adaptation, not a full reproduction of official published benchmark numbers. Validation 275/292 with 17 rejected queries; all accepted Top1 predictions happen to be correct on this split. Source float32 convolution vs streamed sum max difference 3.814697265625e-6, actual top10 ranking identical. Model trained SHA and per-query diagnostics retained locally; public recipe/hashes permit retraining.

## Complexity and image-to-output explanation
Offline encode gallery N descriptors D: O(N) neural inference and O(ND) descriptor storage. A current image is decoded to RGB, normalized/resized, encoded to a descriptor, compared against gallery to produce N similarity scores. Fixed temporal sums only current/past rows along relative-index paths, then ranks scores; adaptive reranks current A candidates and outputs top reference image IDs. Geometry is used only after predictions for evaluation. Temporal score cost O(N*L*|V|), score history O(NL); TopK sort here is O(N log N) because stable full-gallery ranks are retained. Adaptive adds O(NL|V|+N log N), not a new encoding call. SMR four ratios inspect N×L score distances plus a small supervised MLP; its training cost is offline. Encoder, image decoding, transfer, similarity, history and sorting must all enter batch1 deployment timing. Cached score search is not online latency. Index velocity is not physical speed; no navigation accuracy, metric localization RMSE or robot deployment claim.
'''
    url=__import__('subprocess').check_output(['git','remote','get-url','origin'],cwd=ROOT/'third_party/vpr-smr-predictor',text=True).strip()
    method=method.replace('github.com/SoftwareImpacts/S... [exact repository URL in predeclaration/source receipt]',url)
    (docs/'METHOD_V2.md').write_text(method)
    report=f'''# G3 acceptance — implementation passed; scientifically_negative

UTC {utc_now()}. Adaptive run `{adaptive.name}`; SMR adaptation `{smr.name}`; acceptance `{run.id}`. 53 tests pass including original31; independently recounted {checked} metric cells. Exact commands, overrides, versions, source snapshots, hashes and exits in each run. Source pinned SMR uses unchanged selected MIT functions; adaptation differences in METHOD_V2 and predeclaration. No new independent performance read, no old-test tuning, no encoder/network training.

Same 292 validation queries: A210, best fixedT291, adaptive242, fixedTop50T287, fixedTop50lambda.5=277, fixedTop50lambda.75=286; no-continuity248, no-ambiguity261, no-agreement244; SMR first-filter275 (17 abstentions count as misses). All numbers are correct-counts, not percentages. Complete train/validation R1/5/10 and startup/per-query files retained. Train gap medians frozen. Negative hypothesis is accepted as negative, not overwritten with a success narrative. SMR fits only the training window labels; internal oversampled CV cannot validate transfer.

Environment: dedicated .venv-v2-smr installs only imbalanced-learn0.14.0; existing p0 packages read via .pth and unchanged. Failed ensurepip attempt and partial .venv-v2 retained. Source numeric replay agrees top10 with official convolution. New files: adaptive, SMR adapters/runners/predeclarations/tests, acceptance and archive helpers; original source/results/paper unchanged.

Beginner explanation:
1. An image produces a numerical descriptor, not a GPS prediction.
2. The descriptor orders reference pictures by visual similarity.
3. Past score rows vote along reference-index trajectories.
4. Strong fixed trajectory voting already solves almost all validation queries.
5. The new heuristic gives history little weight on many frames and performs worse.
6. Removing components does not demonstrate that the full method works.
7. Related SMR predicts whether to reject a sequence result; rejection still counts as a retrieval miss.
8. We preserve this negative finding and test frozen transfer once.

Auto decision: stop modules, keep single empirical temporal track A; advance G4. Next single task: metadata-audited St Lucia freeze before any retrieval performance, then same-mask comparison and real batch1 timing.
'''
    (docs/'G3_ACCEPTANCE.md').write_text(report)
    for name,text in [('DECISION_LOG.md',f'\n{utc_now()}: G3 adaptive contribution rejected (242 vs291/292); no additional modules. Final paper track A empirical; SMR275/292 is an adaptation only. Independent scores unopened.\n'),
        ('EXPERIMENT_REGISTER.md',f'| G3 | One adaptive rule, ablations, SMR first-filter adaptation | train/val | {adaptive.name}; {smr.name}; {run.id} | scientifically_negative |\n'),
        ('EVIDENCE_INDEX.md',f'\nG3: artifacts/v2/g3/metrics.json (combined), evidence.zip contains both raw per-query files and failed environment logs, SHA256SUMS; local SMR pkl SHA {s["trained_pipeline_sha256"]}.\n')]:
        with (docs/name).open('a') as f:f.write(text)
    folders=[adaptive,smr,run.path]+list((ROOT/'outputs_v2').glob('g3_smr_environment_*'))
    archive('g3',folders,[run.path/'metrics.json',run.path/'checks.json',adaptive/'train_gap_scales.json',smr/'train_class_counts.json'])
    state=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text());state['stages']['G3']='scientifically_negative';state['stages']['G4']='in_progress'
    update_state(ROOT,stages=state['stages'],current_stage='G4',stage_status='in_progress',selected_research_track='A_empirical',
        g3_adaptive_run=adaptive.name,g3_smr_run=smr.name,latest_run_id=run.id)
    (ROOT/'docs/goals/GOAL_V2_STATUS.md').write_text('# VPR-GOAL-V2\n\nG0–G2 passed; G3 scientifically_negative (implementation verified); G4 in progress; G5 pending. Independent performance unopened. Final track: temporal transfer empirical audit, no adaptive superiority claim.\n')
    print(json.dumps({'run':run.id,'stage_status':'scientifically_negative','next':'G4'}),flush=True)

if __name__=='__main__':main()
