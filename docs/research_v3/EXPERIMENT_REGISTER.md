# V3 run register

G0 g0_preserve_20261010T164145Z_7d76bc78 — preservation/regression passed.

- g2_strong_baselines_20261010T165801Z_c7d8c603: FAILED before accuracy (pytest exit 2). New test_core basename collided with original tests/test_core.py. Original failure/log/source/XML retained. Renamed only new V3 test module to test_endpoint_core.py; rerun creates a new directory. No scientific predictions or original files changed.

G2 science run 6eb1c1b3 passed all metric/historical audits; initial backup checkpoint failed filesize guard. g2_backup_repair_20261010T170316Z_27f741cf splits exact ZIP bytes without changing scientific evidence.

Log semantic audit: an early runtime `entrypoint_complete` event was emitted when scientific metrics were sealed, before archive/checkpoint. In the G2 publication failure it is not the whole-process exit code (whole invocation exited1 after the filesize assertion). Original event is preserved and qualified here; actual command/push status and exception receipt take precedence. From G4 onwards, driver.py records the entire child stage subprocess's real exit separately, and finish records only scientific_artifacts_sealed without asserting process success.
