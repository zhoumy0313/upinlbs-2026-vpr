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

### G7 delivery-only font correction

Use `.venv-paper/bin/python -m experiments.endpoint_vpr.g7_delivery_checked` for the final Chinese briefing/archive. Original frozen `final_delivery.py` is retained unchanged; the wrapper corrects verified Latin/numeral glyph gaps only, not predictions, masks, parameters or evaluation. The preserved probe/warnings are outputs_v3/g7_font_preflight_20261010T175729Z_88dcaafd. G2 ordered parts were actually reassembled, whole SHA matched and ZIP test passed in outputs_v3/g7_chunk_restore_audit_20261010T175729Z_37e0cb7c.

### Nonmutating replay command actually checked

`.venv-p0/bin/python -m experiments.endpoint_vpr.replay_seen --dataset St_Lucia --split validation --suite selected`

This runs A, fixedL9, fullL3 and the three frozen selected local policies into a fresh outputs_v3 run; 30 method/radius groups are independently recomputed from new CSV. Actual successful receipt: replay_seen_20261010T180636Z_d400b761, exit0. It does not change phase state, publish into accepted folders, push, or measure online latency. `--suite baselines` replays 16 controls and `--suite grid` the original 224 configurations; these larger replay options were not reexecuted here. Existing original data/weights/score caches with exact identities are still required.

### Public numerical replay without original photos/weights

The one frozen canonical score archive is in artifacts/v3/replay_inputs (two ordered byte parts, total79,569,418 bytes, SHA50527bb46684977bb64e1ac2e102b533aaa217e303a86e0efa3b9f8e0e43b266). It contains CosPlace/EigenPlaces/DINOv2 similarities for one whole St Lucia route and Nordland train/validation plus image IDs/evaluation metadata/model provenance, no photos/descriptors/checkpoints. Numerical experiments can be replayed with Python and NumPy2.2.6; no Torch/GPU is needed for this cached ranking verification.

```bash
.venv-p0/bin/python -m experiments.endpoint_vpr.reassemble artifacts/v3/replay_inputs outputs_v3/my_unique_restore/numerical_inputs.zip
.venv-p0/bin/python -m experiments.endpoint_vpr.public_replay --archive outputs_v3/my_unique_restore/numerical_inputs.zip --dataset St_Lucia --split validation --suite selected
```

Actual restore and replay passed: public_numeric_restore_20261010T1823, public_numeric_replay_20261010T182507Z_b5975a03, six methods/thirty metric groups. --suite baselines or grid reconstructs the original policy sets; --dataset Nordland --split train/validation reconstructs ordinal GT. No phase/push/accepted evidence is changed. Archive SHA/array SHA/canonical shape/dtype and frozen code/configs are checked. Original images, pretrained encoding correctness and real online timing cannot be verified from numerical inputs alone; those require original licensed data/weights/source identities and the G5 recipe. All inputs are already seen; replay does not provide independent validation.
