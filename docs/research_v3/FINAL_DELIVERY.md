# VPR-GOAL-V3 final delivery

Research execution complete with explicit unavailable independent-test scope; Outcome C, novelty_claim_supported=false, formal_submission_ready=false.

Stages G0/G1/G2 pass; G3 scientifically negative; G4 metadata/seen-only freeze pass but independent-data gate unavailable; G5 real-image seen accuracy/timing pass, independent test NOT_RUN; G6 four versioned Working Drafts/PDFs/numeric/literature review; G7 preservation/archive pass.

## Ten scientific judgments
| Item | Evidence/judgment |
|---|---|
| Causal pipeline | Implemented score-only kernels/Strategy/Online; full regression and synthetic tests, source hashes in freeze |
| Repairable endpoint space | Seen H1/r4 oracle369/372 errors, random6; actual eight category-matched examples, not algorithm recall |
| Exceeds strong short-window? | No: P598/656 vs fixed fullL3 641/656 and local fixed blend644/656 at10m |
| Strict/wide retention | Predeclared P gate failed: net−46 strict versus strongest; auxiliary degraded; Nordland loss6 versus L9 |
| Independent task/data | INDEPENDENT_TEST_UNAVAILABLE; Oxford login, SFU official archive errors; no new images/scoring |
| Independent positive contribution | Not measured/not asserted. St Lucia/Nordland remain seen |
| Online added cost | Actual per-method raw4392 timed samples, warm20 and CUDA sync; P mean/median/P95=14.67/14.67/14.86ms; full table in g5 |
| Similar prior work | SeqSLAM/OpenSeqSLAM, STA-VPR/AdaptSeqVPR, SMR and local-image reranking; mechanism matrix distinguishes partial full-text access |
| Defensible contribution | Bounded coverage-versus-policy/baseline/GT/sampling/cost audit; P effective/new-method/generalization claims unsupported |
| Paper status | Working Draft, not formally submission-ready; supervisor/author review recommended |

## Frozen real first-pass seen-stream results
All methods share first8 exclusion and radius-specific no-positive mask; full startup separately. Distances are label distances, not pose RMSE.

| Method | Radius | R@1 correct | Rescue vs A | Harm vs A | median/P90/P95 distance m |
|---|---:|---:|---:|---:|---:|
| A | 10m | 1384/1456 | 0 | 0 | 4.247/7.986/9.869 |
| A | 25m | 1422/1456 | 0 | 0 | 4.247/7.986/9.869 |
| B | 10m | 1397/1456 | 44 | 31 | 4.212/7.787/9.404 |
| B | 25m | 1442/1456 | 27 | 7 | 4.212/7.787/9.404 |
| DINOv2 | 10m | 447/1456 | 9 | 946 | 140.224/699.006/836.351 |
| DINOv2 | 25m | 551/1456 | 7 | 878 | 140.224/699.006/836.351 |
| RRF_k60 | 10m | 1403/1456 | 27 | 8 | 4.211/7.744/9.079 |
| RRF_k60 | 25m | 1441/1456 | 19 | 0 | 4.211/7.744/9.079 |
| AB_0.25 | 10m | 1400/1456 | 23 | 7 | 4.252/7.778/9.484 |
| AB_0.25 | 25m | 1436/1456 | 16 | 2 | 4.252/7.778/9.484 |
| AB_0.5 | 10m | 1408/1456 | 36 | 12 | 4.219/7.636/8.994 |
| AB_0.5 | 25m | 1443/1456 | 23 | 2 | 4.219/7.636/8.994 |
| AB_0.75 | 10m | 1411/1456 | 43 | 16 | 4.218/7.647/8.974 |
| AB_0.75 | 25m | 1447/1456 | 26 | 1 | 4.218/7.647/8.974 |
| fixed_L9 | 10m | 1084/1456 | 47 | 347 | 5.769/15.057/19.211 |
| fixed_L9 | 25m | 1436/1456 | 34 | 20 | 5.769/15.057/19.211 |
| full_L3 | 10m | 1425/1456 | 59 | 18 | 4.220/7.647/8.974 |
| full_L3 | 25m | 1455/1456 | 34 | 1 | 4.220/7.647/8.974 |
| full_L5 | 10m | 1416/1456 | 57 | 25 | 4.278/7.846/9.104 |
| full_L5 | 25m | 1456/1456 | 34 | 0 | 4.278/7.846/9.104 |
| full_L9 | 10m | 1388/1456 | 56 | 52 | 4.454/8.649/9.922 |
| full_L9 | 25m | 1455/1456 | 34 | 1 | 4.454/8.649/9.922 |
| global_fixed_L9_blend_0.25 | 10m | 1414/1456 | 42 | 12 | 4.141/7.399/8.636 |
| global_fixed_L9_blend_0.25 | 25m | 1452/1456 | 32 | 2 | 4.141/7.399/8.636 |
| global_fixed_L9_blend_0.5 | 10m | 1397/1456 | 54 | 41 | 4.144/7.849/9.298 |
| global_fixed_L9_blend_0.5 | 25m | 1453/1456 | 33 | 2 | 4.144/7.849/9.298 |
| global_fixed_L9_blend_0.75 | 10m | 1296/1456 | 54 | 142 | 4.441/10.505/13.548 |
| global_fixed_L9_blend_0.75 | 25m | 1449/1456 | 34 | 7 | 4.441/10.505/13.548 |
| shuffled_full_L9_seed0 | 10m | 837/1456 | 28 | 575 | 7.981/39.026/55.167 |
| shuffled_full_L9_seed0 | 25m | 1191/1456 | 22 | 253 | 7.981/39.026/55.167 |
| reversed_fixed_L9 | 10m | 61/1456 | 1 | 1324 | 140.549/481.625/672.490 |
| reversed_fixed_L9 | 25m | 144/1456 | 4 | 1282 | 140.549/481.625/672.490 |
| P_fixed_L9_H3_r1_e0.06 | 10m | 1315/1456 | 52 | 121 | 4.390/9.876/12.728 |
| P_fixed_L9_H3_r1_e0.06 | 25m | 1449/1456 | 34 | 7 | 4.390/9.876/12.728 |
| R1_full_L3_H1_r1 | 10m | 1410/1456 | 43 | 17 | 4.264/7.842/9.228 |
| R1_full_L3_H1_r1 | 25m | 1455/1456 | 34 | 1 | 4.264/7.842/9.228 |
| R2_full_L3_H3_r1_g0.75 | 10m | 1431/1456 | 57 | 10 | 4.188/7.402/8.685 |
| R2_full_L3_H3_r1_g0.75 | 25m | 1456/1456 | 34 | 0 | 4.188/7.402/8.685 |
| P_epsilon_zero | 10m | 1084/1456 | 47 | 347 | 5.769/15.057/19.211 |
| P_epsilon_zero | 25m | 1436/1456 | 34 | 20 | 5.769/15.057/19.211 |
| R1_same_P_pool | 10m | 1404/1456 | 38 | 18 | 4.205/7.849/9.095 |
| R1_same_P_pool | 25m | 1451/1456 | 30 | 1 | 4.205/7.849/9.095 |
| R3_same_P_radius | 10m | 1354/1456 | 49 | 79 | 4.360/9.035/11.079 |
| R3_same_P_radius | 25m | 1442/1456 | 32 | 12 | 4.360/9.035/11.079 |

## Delivery files
- New paper: paper/revisions/v3_r04/main.tex and main.pdf; all v3_r01–r04 preserved with numeric_bindings, table_cells, figure data and version change maps.
- Old papers remain paper/main.pdf, paper/versions/v1_20261010_frozen/, paper/revisions/v2_*/ and paper/submission_candidate/v2/; byte-preservation inventory in artifacts/v3/g0/old_files.json.
- Full stage public archives/parts in artifacts/v3/, final complete-text receipts plus SHA index and archive chain in artifacts/v3/final/. Original photos/large arrays/weights remain local with source/hash identities, excluded from redistribution.
- Exact command logs with true exits, source snapshots, failures and raw first-pass/latency/TopK/candidate/eligible/winning-path/GT distance evidence in outputs_v3; complete public ledgers reside in stage archives.
- AUTHOR_SUMMARY_ZH.md/pdf (<=2 pages), AUTHOR_REVIEW_CHECKLIST.md, LITERATURE_MATRIX.md, REPRODUCE.md, EVIDENCE_MAP.md, all Gx_ACCEPTANCE reports and mutable state.

No training, driver/system/account change, main/V2 merge/force-push, external-test tuning, author decision, paid GPU, signature or formal submission occurred. A working empirical paper with an unsupported method mechanism has uncertain conference value; obtain supervisor approval of contribution and credible new validation before presenting it as a successful new method. New independent data would need a new source audit/freeze before predictions, not post-test parameter edits.

## Closing receipt and author-friendly briefing
Preferred Chinese briefing: AUTHOR_SUMMARY_ZH_r02.pdf (actual page count and unsplit numeric identifiers checked in AUTHOR_BRIEF_REFLOW_AUDIT.json). Original AUTHOR_SUMMARY_ZH.pdf/md remain unchanged. This is layout only. All completed G7 driver/checkpoint/log/source receipts are additionally in artifacts/v3/final/closing_receipts.zip; CLOSING_RECEIPT.json adds original G0/G1 ZIP identities, checkpoint index and text-credential scan. GOAL_V3_STATE.last_pushed_sha refers to the verified scientific checkpoint, not its own later metadata commit. The post-push HEAD/remote proof lives in outputs_v3/g7_closing_receipts_20261010T184014Z_8c462cd5/actual_post_push_verification.json.
