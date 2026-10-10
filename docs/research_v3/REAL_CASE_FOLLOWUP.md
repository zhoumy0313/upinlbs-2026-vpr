# Frozen real-image followup of all eight preselected cases

No query/category was reselected after seeing P. All distances use10m geographic label truth offline, not pose accuracy.

| q | Original category | A m | L9 m | L3 m | P m | C positive? | Eligible positive? |
|---|---|---:|---:|---:|---:|---|---|
| 8 | repairable_H1_r4 | 4.054 | 12.373 | 4.054 | 12.373 | True | True |
| 16 | repairable_H1_r4 | 6.852 | 21.803 | 6.852 | 21.803 | True | False |
| 9 | unrepairable_H1_r16 | 2.708 | 25.213 | 2.422 | 2.708 | True | True |
| 10 | unrepairable_H1_r16 | 2.999 | 11.581 | 2.178 | 11.581 | False | False |
| 17 | A_correct_T_wrong | 6.852 | 22.400 | 6.852 | 2.450 | True | True |
| 18 | A_correct_T_wrong | 6.936 | 11.430 | 6.936 | 11.430 | True | False |
| 11 | multiwindow_disagreement | 4.795 | 9.931 | 7.296 | 9.931 | True | True |
| 12 | multiwindow_disagreement | 4.891 | 8.578 | 4.891 | 8.578 | True | True |

Actual IDs, candidate/eligible indices and winning paths: g6_actual_case_followup_20261010T182931Z_fce5ce1d/actual_cases.json; G5 actual CSV SHA stored in raw_metrics.json. The H1/r16 unavailable case label is a specific diagnostic pool, not a claim that every H3 or short-window policy must fail. Query9 is recovered by P through a different coarse hypothesis; P still fails several available neighborhoods. Successful/bad cases support limits, not an unvalidated positive mechanism claim.

Two actual success mechanisms: q9 is repaired through another H3 coarse endpoint despite the H1 diagnostic pool failing; q17 is rescued by visual reranking within support (22.400m to2.450m). Failure mechanisms: q8 contains an admissible positive but ranks a wrong eligible reference first; q16/q18 contain positives rejected by temporal support; q10 has no positive in the selected candidate pool. These are descriptive explanations of frozen records, not grounds for further tuning.
