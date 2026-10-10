# G5 acceptance
1. Added actual image Online pipeline and immutable real timing run.
2. Each image is reopened/decoded, each required frozen encoder runs at batch1, descriptor transfers to CPU, exact similarity computed, causal history updated and complete gallery sorted. GPS is evaluation-only.
3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g5`; worker runs with OMP/BLAS/PyTorch threads=1 and CUDA synchronization. 20 warm images + three full 1464-query passes for every frozen comparison, startup included. Gallery encoding and model loading measured separately.
4. All methods R@1/5/10 and 10/25/5/15/50m labels from first real pass; paired counts/quantiles and measured mean/median/P95 are independently rebuilt from CSV. RSS, CUDA allocated/reserved separate.
5. Frozen method/mask/GT/model parameters, no changes using outcomes; all data explicitly seen.
6. INDEPENDENT_TEST_UNAVAILABLE: no external recall invented; real timing and seen audit executed. Development mechanism judgment remains unchanged.
7. Warm OS cache/unlocked clocks/correlated video; small latency deltas are descriptive, no deployment or significance claim.
8. Source/raw timings/real prediction ledger/negative controls/failures/hashes archived; push follows.
9. Next: evidence-driven V3 manuscript versions and numeric/literature/PDF audit, retain working_draft if external validation absent.


Run g5_real_online_20261010T175234Z_dfcec131; archive SHA 3cf2980cc7404dd555b2da9ca81e068925e5fd0400c5af183d2ba5852b429e9c; ordered parts and exact hashes in archive_manifest.json. Exact commands/exits/logs in archive. Checkpoint follows; push receipt is separate.
