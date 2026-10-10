# Predeclared radius sensitivity and overall Outcome C

UTC 2026-10-10T15:10:21.025541+00:00, `g4_transfer_sensitivity_audit_20261010T151020Z_c0f74699`. Raw frozen primary evaluator label B refers to25m. Its results are immutable. Overall audited outcome C reflects instability under the prescribed10/25/50m tolerances. This is a conservative interpretation, not a change of primary metric or method.

| Method | R@1 10m | R@1 25m primary | R@1 50m |
|---|---:|---:|---:|
| A-only | 1384/1456 (95.05%) | 1422/1456 (97.66%) | 1426/1456 (97.94%) |
| B-only | 1397/1456 (95.95%) | 1442/1456 (99.04%) | 1442/1456 (99.04%) |
| RRF_k60 | 1403/1456 (96.36%) | 1441/1456 (98.97%) | 1442/1456 (99.04%) |
| AB_fixed_0.75 | 1411/1456 (96.91%) | 1447/1456 (99.38%) | 1447/1456 (99.38%) |
| fixed_T_best | 1084/1456 (74.45%) | 1436/1456 (98.63%) | 1456/1456 (100.00%) |
| fixed_blend_best | 1296/1456 (89.01%) | 1449/1456 (99.52%) | 1456/1456 (100.00%) |
| adaptive_full | 1389/1456 (95.40%) | 1439/1456 (98.83%) | 1440/1456 (98.90%) |
| SMR_first_filter_adapted | 1253/1456 (86.06%) | 1451/1456 (99.66%) | 1456/1456 (100.00%) |

All tolerances use1456 queries: no no-positive exclusions at any radius, common startup8. Selected fixedT net correct counts are -300/+14/+30 versus A at10/25/50m. Its 25m gain cannot establish uniformly improved geographic retrieval. The heuristic is still below strong fixed/static controls under the primary comparison and failed development superiority.

GPS separation statistics describe retrieved reference labels, not localization RMSE or deployed pose accuracy. Index-velocity mismatch and score averaging can shift endpoints; a causal mechanism is a hypothesis, not independently proven here. No method is fitted to the exposed test. Broad-velocity L5 perfect25m row remains sensitivity, never a new selected winner.

Timing caveats: dual encoders prepare tensors separately, warm file cache, one CPU/BLAS thread, no locked clocks; source SMR feature loops included, so predictor-only published milliseconds are not directly comparable. Actual descriptors match cached batch1 exactly, score differences≤1.1102230246251565e-15 and all nine methods/three repeats have zero top10 ranking mismatches.

The original G4 figure point file uses a generic historical field named value_percent, including latency rows; their metric names and plot axes already specify milliseconds. A derived figure_points_with_units.csv provides explicit units and preserves all original values and the immutable file. This is a metadata clarification, not a result or algorithm correction.
