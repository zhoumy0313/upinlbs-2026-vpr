# V3 run register

G0 g0_preserve_20261010T164145Z_7d76bc78 — preservation/regression passed.

- g2_strong_baselines_20261010T165801Z_c7d8c603: FAILED before accuracy (pytest exit 2). New test_core basename collided with original tests/test_core.py. Original failure/log/source/XML retained. Renamed only new V3 test module to test_endpoint_core.py; rerun creates a new directory. No scientific predictions or original files changed.

G2 science run 6eb1c1b3 passed all metric/historical audits; initial backup checkpoint failed filesize guard. g2_backup_repair_20261010T170316Z_27f741cf splits exact ZIP bytes without changing scientific evidence.

Log semantic audit: an early runtime `entrypoint_complete` event was emitted when scientific metrics were sealed, before archive/checkpoint. In the G2 publication failure it is not the whole-process exit code (whole invocation exited1 after the filesize assertion). Original event is preserved and qualified here; actual command/push status and exception receipt take precedence. From G4 onwards, driver.py records the entire child stage subprocess's real exit separately, and finish records only scientific_artifacts_sealed without asserting process success.

- Native r03 failed on unescaped path_offsets underscore; failed source and actual diagnostics preserved (g6_native_source_repair_20261010T182336Z_3c0d0e54; paper/revisions/v3_r03/native_compile_failure_01.json). Only new TeX rendering changed; r03/r04 native compile succeeded after one repair. Initial native-success metadata parse error preserved/corrected in g6_native_receipt_parse_repair_20261010T182507Z_c2c985fd (actual compiler response was success).
- G5 entire driver actual_exit_code=0, all110 groups audit passed, cached/repeat Top10 mismatch0, maxscore difference1.1102230246251565e-15.
- Portable numerical inputs pack driver exit0; reassembled SHA exact and public numerical replay six policies/30 groups passed. These are cached ranking proofs, never real latency or new independent testing.
