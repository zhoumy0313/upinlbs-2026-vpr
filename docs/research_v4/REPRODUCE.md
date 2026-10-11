# V4 reproduction

Use pinned .venv-p0 and existing official model source commits/checkpoints in configs/model_sources.json. Raw sources and actual SHA in DATA_MANIFEST_r02.json. All arrays remain local; feature_manifest.json binds every row, image SHA, model state/adapter/preprocessing and descriptor SHA. Fixed protocol and grid are in configs/v4; immutable freeze binds the exact science.

## Local already-run audit

```bash
cd /home/aaron/upinlbs_vpr/upinlbs_vpr_starter
.venv-p0/bin/python experiments/temporal_alignment_v4/replay.py --cached
```

## Numeric evidence on a fresh checkout

Every evidence.zip under artifacts/v4 is a normal ZIP (LZMA). Check archive_manifest.json SHA256 first, then use Python zipfile to extract into a fresh separate evidence directory. Original relative outputs_v4 paths, per_query.csv, run_meta.json, run_config.yaml, source snapshots, stdout/stderr and SHA256SUMS are retained. Use independent evaluate.audit_csv with raw_metrics results. Large npy/npz arrays and raw images are not included in public ZIPs; rebuild with features.encode and the exact descriptor_rows/full image manifest, original frozen source/model/checkpoints and official image hashes. Rebuilt extraction must be labelled replay of a now-seen test, never a new blind test. Parent execution runs retain actual whole-process exit codes.

Do not run run_g4_test.py again: its first-open guard prevents rewriting the blind-test record. New scientific changes require new protocol/version and independent collection. No driver/system/SSH/proxy reinstall is needed.
