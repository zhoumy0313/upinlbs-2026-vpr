# G1 acceptance — passed with disclosed literature access limitations

Date: 2026-10-10T13:28:01.563055+00:00. Existing 31 tests and V2 tests all pass: 38 total. Development data: 600 train / 300 validation, gallery 1750. No final-test threshold choice or independent score reading. Source/code/inputs: run manifests, strict encoder fingerprints, per-query.csv, data_audit.json, SHA-256 files in artifacts/v2/g1. Negative original DINOv2 caches remain; stale extraction-source fingerprints were rejected and new descriptors built in outputs_v2. Actual commands and zero exits: diagnosis and acceptance commands.jsonl; source access failures retained separately. The first G0 ROS failure remains unchanged.

G1_DIAGNOSIS.md gives the actual R@K, oracle, rank-error counts, examples and GT limitations. RELATED_WORK_MATRIX.md records method/results reading and partial original-paper access explicitly; no full-text claim for inaccessible papers. Original V1 files/results/paper remain unchanged. New files: diagnostics, G1 source/metadata/release scripts and tests, V2 docs and public numeric evidence. Reproduce: `.venv-p0/bin/python experiments/temporal_vpr/run_g1.py` creates a new unique run; test isolation overrides are in argv.json.

Beginner explanation:
1. A photograph enters a frozen encoder and becomes a normalized numeric vector.
2. The vector is compared with all 1750 summer reference vectors.
3. Similarity sorting produces candidate image IDs, not GPS coordinates.
4. Offline labels tell us the first rank with a correct reference within ±5 frames.
5. R@10 is a candidate upper bound, not a new algorithm score.
6. Past observations may help reject visually similar wrong railway scenes.
7. Exact duplicates and station ambiguity require careful GT interpretation.
8. G2 will test this temporal hypothesis without giving GT to the matcher.

Decision: G1 permits bounded baseline exploration; detailed inaccessible-paper comparisons remain a novelty-audit limitation. Next single task: G2 fixed causal temporal and static fusion baselines plus mandatory causal/integration checks. Research mainline still not selected; independent performance unopened.
