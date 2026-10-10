# V3 reproduction entry

Repository branch: research/vpr-v3-endpoint-refinement, rooted exactly at V2 81fbf62dfaf5cdd28a005afbe6853289524b4d4d. Original data/weights/caches are local and intentionally absent from Git; their original source/checkpoint/image identities remain in V2 receipts and the V3 G0 inventory. Model/data provenance must match before replay.

From /home/aaron/upinlbs_vpr/upinlbs_vpr_starter:

```bash
PYTHONPATH='' PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-v2-smr/bin/python -m pytest tests experiments/temporal_vpr/tests experiments/endpoint_vpr/tests experiments/paper_v2/test_manuscript_audit.py -q
.venv-p0/bin/python -m experiments.endpoint_vpr.run_g1
.venv-p0/bin/python -m experiments.endpoint_vpr.run_g2
.venv-p0/bin/python -m experiments.endpoint_vpr.run_g3
```

Stage entrypoints retain unique raw runs but their one-time publication directory intentionally refuses overwrite. On an already completed branch, use the immutable source_snapshot in a fresh V3 replay checkout or call the pure datasets/predictions/evaluate/audit functions to a new Run. Do not rerun G0 initialization, replace accepted artifacts, or silently reopen a future independent test. Runtime checkpoint and G4/G5 entrypoints advance the authorized state and perform V3 branch backup; they are not generic blind replay commands. Source snapshots and commands retain the exact version that generated each run.

To restore a public multipart archive without any dataset/model:

```bash
.venv-p0/bin/python -m experiments.endpoint_vpr.reassemble artifacts/v3/g2_backup_repair outputs_v3/restored_g2_unique/evidence.zip
```

The destination must be new. Restore verifies every part's size/SHA, whole ZIP SHA and ZIP integrity. Other stage folders carry archive_manifest.json with the same convention. Original oversized G2 evidence.zip remains locally unchanged; its exact Git parts are the remote backup. No part exceeds48MiB. Final index maps every public archive to the original scientific run and hashes.

Actual online timing uses frozen real images/encoders, never cached features. `.venv-p0/bin/python -m experiments.endpoint_vpr.driver experiments.endpoint_vpr.run_g5` records the whole-stage exit and its command/environment overrides; internal worker executes warm20 plus three full passes. It requires the existing model/source/image hashes and frozen code, and may be long. The external test is explicitly NOT_RUN when source unavailable; no local replay grants St Lucia independence.

V3 manuscripts are standalone main.tex with embedded bibliography and vector diagrams; references.tex is an archival bibliography copy, not a build dependency. Native compile_latex_document checks each saved source. Exact PDF exports are from new V3-only standard public GitHub CI; Poppler checks pages/fonts/text locally, without installing a local TeX toolchain. All earlier paper versions remain read-only.
