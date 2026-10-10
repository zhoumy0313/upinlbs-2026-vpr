# G0 acceptance — passed

UTC: 2026-10-10T13:12:43.587905+00:00. Baseline: `78eb9e45d3bc469630b0c46ad1ea02b318ee151b`; branch: `research/temporal-vpr-v2`.

Preserved 1470 original tracked/output files with SHA-256 inventory; old main, scientific source/protocol/results/evidence and paper/main.* unchanged. .gitignore only gained V2 exclusions. Frozen tag and exact human-readable V1 paper snapshot exist. Disk/network/GPU probe command exits are zero in the successful run. No drivers, SSH, proxy, system Python or ROS changed.

Runs: `outputs_v2/g0_preserve_20261010T130954Z_842e31e4` (pytest startup failure retained); `outputs_v2/g0_regression_20261010T131233Z_697c38c9` (successful isolated regressions).
Tests: 34 passed; failures/errors: 0/0. Includes 31 original tests and 3 V2 runtime/preservation tests.

Commands/exit codes: both runs' commands.jsonl; successful stdout.log/stderr.log; original ROS plugin failure stderr.log. Inputs: docs/goals/v1_baseline_state.json and full inventory; inventory SHA `eff8e810d9f2e8d8ff50526ccaed4e16afd55a8257ae303653dec6d2db32d9e7`. Public archive: artifacts/v2/g0/evidence.zip, SHA `565bb731d32e6f50b006bf1de1396ef01b69037568e78e2db0d4d31a6bfc1cda`. No VPR metric or new model has been evaluated. No test-label tuning. Original old metrics remain unchanged.

New files: docs/goals and docs/research_v2 scaffolding, AGENTS_V2.md, scoped experiments/temporal_vpr code/tests, paper/versions/v1_20261010_frozen; .gitignore append.
Reproduction: `.venv-p0/bin/python experiments/temporal_vpr/finish_g0.py (one-time G0 publisher; refuses existing archive; use recorded pytest command for regression replay)`.

## Beginner explanation
1. Old photographs, descriptors and scores are unchanged input assets.
2. File hashes identify the exact bytes used in the first study.
3. A Git tag names the old source snapshot permanently.
4. A new branch holds new research while main retains the old version.
5. The regression suite checks retrieval/gating behavior without new final-image evaluation.
6. Process isolation prevents unrelated ROS plugins from affecting this project.
7. This stage outputs preservation evidence, not improved recognition numbers.
8. Oracle and temporal ideas will first be audited on train/validation in G1.

Decision: accept G0; next single task: G1 GT/order, development candidate potential and primary-literature audit. New independent performance remains unopened.
