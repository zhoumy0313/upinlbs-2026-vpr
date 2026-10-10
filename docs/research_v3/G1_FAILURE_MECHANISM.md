# G1 acceptance
1. Added V3 score-only temporal/candidate/refinement kernels, provenance loader, 10 synthetic unit tests and diagnostics. Original files untouched.
2. Images were encoded in V2; verified cached current visual scores produce causal T; bounded neighbors are inspected by offline GT only. Oracle is an upper bound, not prediction. Actual image inputs and eight ordered cases are in real_cases.json/local contact sheet.
3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g1`; CPU cached diagnostics, original pretrained GPU models unchanged. Initial ad-hoc pytest exit 1 (ROS plugin needs lark); captured reproduction also retained. With PYTEST_DISABLE_PLUGIN_AUTOLOAD=1/PYTHONPATH='', 10 tests pass. No ROS/system change.
4. T errors=372; r4/H1 oracle repairs=369; equal-size random=6; coverage=0.991935. All H/r, thresholds, pairs, quantiles and top10 ledgers retained; independent CSV audit passes.
5. A/T/L3/L5/L9 have identical first-eight exclusion and radius-specific no-positive masks. All data seen.
6. H1 gate=True; proceed only with finite predeclared P search if true. No optional module if true.
7. St Lucia rounded UTM discrepancy up to 1.48305m; ±2m threshold band reported. Nordland ordinal GT is not metres. Local photographs are not redistributed.
8. Source snapshots, hashes and command exit codes accompany this run; checkpoint/push receipt follows.
9. Next: reproduce all strong baselines and historical V2 top1 identities before bounded grid.

See coverage_summary.json, reference_spacing.json and per_query.csv in the G1 archive.
