# G3 acceptance — implementation passed; scientifically_negative

UTC 2026-10-10T14:02:12.174244+00:00. Adaptive run `g3_adaptive_development_20261010T134356Z_93dbfee7`; SMR adaptation `g3_smr_adaptation_20261010T135720Z_bcbbf327`; acceptance `g3_acceptance_20261010T140208Z_5ab06d53`. 53 tests pass including original31; independently recounted 48 metric cells. Exact commands, overrides, versions, source snapshots, hashes and exits in each run. Source pinned SMR uses unchanged selected MIT functions; adaptation differences in METHOD_V2 and predeclaration. No new independent performance read, no old-test tuning, no encoder/network training.

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
