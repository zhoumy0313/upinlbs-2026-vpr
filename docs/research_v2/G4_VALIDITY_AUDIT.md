# G4 validity audit — passed with scientific limitations

216 R@1/5/10 cells independently recounted from actual per-query CSV, paired rescue/harm recounted. 39528 real-image timing records independently recomputed mean/median/P95. 56 original/V2 tests pass. All immutable freeze code/config/model/data/galleries/SMR hashes verify; freeze timestamp precedes first performance opening. Accuracy/timing commands exit0 and source snapshots retained. No old final-test selection, no new-test tuning, no network training; SMR small classifier supervised train only. Common closed-set and shared-startup masks disclosed and same for all comparisons.

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

Decision: accept G4 evidence, Outcome B; auto-advance G5 empirical manuscript versions, numerical mapping, native compilation and readiness judgement. Single next task: versioned evidence-backed empirical paper, no new method family.

## Overall sensitivity qualification

The automated Outcome B above is specific to primary25m. Predeclared10m reverses selected fixedT gains (-300 versus A); overall audited outcome C, unstable transfer. Original predictions/config/metrics remain unchanged. See G4_SENSITIVITY_ANALYSIS.md and `g4_transfer_sensitivity_audit_20261010T151020Z_c0f74699`.
