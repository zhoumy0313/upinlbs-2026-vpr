# G2 acceptance — passed

Date: 2026-10-10T13:38:19.614243+00:00. Data run `g2_strong_baselines_20261010T133356Z_5d8c3f15`; acceptance run `g2_acceptance_20261010T133813Z_d6200bfc`. Actual 49 tests pass, including original 31; ten causal/ranking tests, runtime/diagnostic/plot tests and real-image CPU/GPU/cached replay integration. Independent verification recounts 540 Recall cells from per_query.csv; full manifest shuffle aligns by explicit image IDs. Mandatory causal checks include L1 identity, no future, resets, whole invalid path, no online GT/filename input, manual T, shuffle control and common query masks. No test-based tuning.

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
