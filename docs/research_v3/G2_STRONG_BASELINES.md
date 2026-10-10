# G2 acceptance
1. Added strong_baselines run using V3 score-only Strategy, no old-source edits.
2. Verified old score hashes and canonical image IDs; reset at each split; produce full ranking then evaluate GT offline. A is one image descriptor; T uses only prior/current scores; local policies rerank bounded indices.
3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g2`; actual tests and CPU accuracy commands are in logs; no cached timing claims.
4. Strong controls: single CosPlace/EigenPlaces/DINOv2, RRF, three A+B fusions, L9-v1.2, full L3/L5/L9, three global blends, shuffled and reversed controls, simple H1-r4 snap and local fixed blend.

| Method | Correct | 10m % | Rescue | Harm |
|---|---:|---:|---:|---:|
| A | 621/656 | 94.66 | 0 | 0 |
| B | 635/656 | 96.80 | 25 | 11 |
| DINOv2 | 229/656 | 34.91 | 5 | 397 |
| RRF_k60 | 630/656 | 96.04 | 14 | 5 |
| AB_0.25 | 631/656 | 96.19 | 12 | 2 |
| AB_0.5 | 636/656 | 96.95 | 19 | 4 |
| AB_0.75 | 639/656 | 97.41 | 24 | 6 |
| fixed_L9 | 495/656 | 75.46 | 22 | 148 |
| full_L3 | 641/656 | 97.71 | 27 | 7 |
| full_L5 | 638/656 | 97.26 | 25 | 8 |
| full_L9 | 626/656 | 95.43 | 24 | 19 |
| global_fixed_L9_blend_0.25 | 636/656 | 96.95 | 17 | 2 |
| global_fixed_L9_blend_0.5 | 634/656 | 96.65 | 26 | 13 |
| global_fixed_L9_blend_0.75 | 593/656 | 90.40 | 25 | 53 |
| shuffled_full_L9_seed0 | 379/656 | 57.77 | 13 | 255 |
| reversed_fixed_L9 | 20/656 | 3.05 | 0 | 601 |
| R3_fixed_L9_H1_r4 | 604/656 | 92.07 | 12 | 29 |
| R2_fixed_L9_H1_r4_g0.5 | 621/656 | 94.66 | 26 | 26 |

5. Same radius-specific no-positive mask and eight-query startup exclusion; full-stream results retained. St Lucia validation is seen/exploratory.
6. All required historical top10s agree exactly; Nordland validation counts agree with original cache runs. Independent scalar rank and CSV R@K/paired/quantile checks pass.
7. GT rounding and video correlation prohibit pose/significance claims. No independent-test scores opened.
8. Source/identities/CSV/logs in public archive; exact push receipt follows.
9. Next: execute predeclared finite grid, compare P with strongest fixed and simple local controls.
