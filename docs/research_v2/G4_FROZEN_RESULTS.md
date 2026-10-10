# G4 frozen independent results

UTC 2026-10-10T15:07:33.405505+00:00. Freeze `v2_20261010T143902Z` at 2026-10-10T14:39:03.023773+00:00; first independent access 2026-10-10T14:39:59.011566+00:00. Code commit ae41a7c038e2da9ba83fc878fe428a49e332859d. Evaluation `g4_independent_evaluation_20261010T143959Z_73e61bb4`, real-image timing `g4_real_online_latency_20261010T144339Z_bb8f86bb`, audit `g4_acceptance_20261010T150725Z_c4fe2906`. No parameters changed after opening.

Official St Lucia subset: gallery 1549, query 1464; primary closed-set/common queries 1456. Offline UTM zone56J radius≤25m; sensitivities10/50m predeclared. Every method uses same GT/mask. All excluded no-positive IDs and eight startup frames retained in per-query ledger. Neither UTM nor filename fields are matcher inputs.

| Method | R@1 | R@5 | R@10 | Rescue / harm | Rejected |
|---|---:|---:|---:|---:|---:|
| A-only | 1422/1456 (97.66%) | 1449/1456 (99.52%) | 1452/1456 (99.73%) | 0/0 | 0 |
| B-only | 1442/1456 (99.04%) | 1452/1456 (99.73%) | 1456/1456 (100.00%) | 27/7 | 0 |
| DINOv2-only | 551/1456 (37.84%) | 864/1456 (59.34%) | 1007/1456 (69.16%) | 7/878 | 0 |
| RRF_k60 | 1441/1456 (98.97%) | 1454/1456 (99.86%) | 1456/1456 (100.00%) | 19/0 | 0 |
| AB_fixed_0.25 | 1436/1456 (98.63%) | 1453/1456 (99.79%) | 1455/1456 (99.93%) | 16/2 | 0 |
| AB_fixed_0.5 | 1443/1456 (99.11%) | 1454/1456 (99.86%) | 1456/1456 (100.00%) | 23/2 | 0 |
| AB_fixed_0.75 | 1447/1456 (99.38%) | 1455/1456 (99.93%) | 1456/1456 (100.00%) | 26/1 | 0 |
| fixed_T_best | 1436/1456 (98.63%) | 1455/1456 (99.93%) | 1456/1456 (100.00%) | 34/20 | 0 |
| fixed_blend_best | 1449/1456 (99.52%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 34/7 | 0 |
| full_velocity_T_L3 | 1455/1456 (99.93%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 34/1 | 0 |
| full_velocity_T_L5 | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 34/0 | 0 |
| full_velocity_T_L9 | 1455/1456 (99.93%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 34/1 | 0 |
| shuffled_L9 | 1191/1456 (81.80%) | 1395/1456 (95.81%) | 1434/1456 (98.49%) | 22/253 | 0 |
| velocity08_L9 | 1352/1456 (92.86%) | 1454/1456 (99.86%) | 1456/1456 (100.00%) | 32/102 | 0 |
| velocity10_L9 | 1451/1456 (99.66%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 34/5 | 0 |
| reverse_velocity_L9 | 144/1456 (9.89%) | 324/1456 (22.25%) | 484/1456 (33.24%) | 4/1282 | 0 |
| adaptive_full | 1439/1456 (98.83%) | 1453/1456 (99.79%) | 1455/1456 (99.93%) | 17/0 | 0 |
| remove_continuity | 1440/1456 (98.90%) | 1453/1456 (99.79%) | 1455/1456 (99.93%) | 18/0 | 0 |
| remove_ambiguity | 1448/1456 (99.45%) | 1454/1456 (99.86%) | 1456/1456 (100.00%) | 29/3 | 0 |
| remove_agreement | 1441/1456 (98.97%) | 1454/1456 (99.86%) | 1455/1456 (99.93%) | 19/0 | 0 |
| fixed_lambda1_Top50 | 1444/1456 (99.18%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 33/11 | 0 |
| fixed_lambda05_Top50 | 1452/1456 (99.73%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 32/2 | 0 |
| replace_adaptive_with_G2_fixed_lambda | 1450/1456 (99.59%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 33/5 | 0 |
| SMR_first_filter_adapted | 1451/1456 (99.66%) | 1456/1456 (100.00%) | 1456/1456 (100.00%) | 34/5 | 0 |

| Real batch1 method | Mean ms | Median ms | P95 ms |
|---|---:|---:|---:|
| A-only | 10.879 | 10.832 | 11.139 |
| B-only | 14.000 | 14.001 | 14.273 |
| DINOv2-only | 14.276 | 14.268 | 14.694 |
| RRF_k60 | 23.171 | 23.176 | 23.473 |
| AB_fixed_0.75 | 22.954 | 22.979 | 23.339 |
| fixed_T_best | 11.415 | 11.419 | 11.679 |
| fixed_blend_best | 11.304 | 11.306 | 11.554 |
| adaptive_full | 11.668 | 11.670 | 11.949 |
| SMR_first_filter_adapted | 73.873 | 74.187 | 75.307 |

Outcome B: fixed temporal improves over single image here, but own adaptivity did not beat mature temporal on development; only empirical temporal conclusions are justified.

All 24 methods ×3 radii, weight/window/velocity/reverse/shuffle sensitivities and shared-query startup results are retained in metrics.json. Contiguous100-query block paired net counts are descriptive, not independent confidence intervals. Figure points and table cells have exact source hashes. Any uncertainty in frame-based Nordland GT and geographic St Lucia loop ambiguity remains a limitation.

Real latency includes image open/RGB decode, tensor normalization/resize, model batch1, CPU transfer, gallery similarity, history and ranking; warmed20 and three full1464-query traversals per method, CUDA synchronized, clocks not locked. Timed computation does not read cached query descriptors/scores; cached values are used only for post-timer identity audits. Offline gallery batch16 build and bytes separate. RSS includes accuracy-audit arrays and allocator/cached memory; CUDA allocated/reserved values are not total device use. Avoid significance claims for small latency differences.

Precision checks (including any real-vs-cache ranking disagreement) are included verbatim in latency metrics; no hidden correction or selective rerun. SMR is the declared first-filter code adaptation trained only on Nordland; rejects count as misses. No full published reproduction or novel superiority claim. Original old-test tables remain post_hoc/seen V1 evidence only.

## Overall sensitivity qualification

The automated Outcome B above is specific to primary25m. Predeclared10m reverses selected fixedT gains (-300 versus A); overall audited outcome C, unstable transfer. Original predictions/config/metrics remain unchanged. See G4_SENSITIVITY_ANALYSIS.md and `g4_transfer_sensitivity_audit_20261010T151020Z_c0f74699`.
