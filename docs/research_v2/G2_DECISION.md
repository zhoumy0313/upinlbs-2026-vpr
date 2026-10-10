# G2 strong baseline results — development only

Run: `g2_strong_baselines_20261010T133356Z_5d8c3f15`, source/count hashes in artifacts/v2/g2. All rows share 292 validation queries, gallery 1750, ±5 ordinal-frame GT; full 300-query startup results remain separate in metrics.json.

| Method | R@1 | R@5 | R@10 | Rescue / harm versus A |
|---|---:|---:|---:|---:|
| A-only | 71.92% | 91.78% | 97.26% | 0 / 0 |
| B-only | 84.59% | 95.55% | 97.60% | 50 / 13 |
| DINOv2-only | 52.05% | 75.68% | 83.22% | 28 / 86 |
| RRF_k60 | 83.22% | 95.55% | 98.63% | 43 / 10 |
| AB_fixed_0.25 | 84.25% | 95.55% | 98.29% | 41 / 5 |
| AB_fixed_0.5 | 85.27% | 96.23% | 98.63% | 47 / 8 |
| AB_fixed_0.75 | 85.62% | 95.21% | 97.60% | 50 / 10 |
| shuffled_L9 | 81.51% | 90.41% | 94.52% | 61 / 33 |
| temporal_L9_v1.2_lambda1 | 99.66% | 100.00% | 100.00% | 82 / 1 |
| temporal_L3_v0.8,1.0,1.2_lambda1 | 84.59% | 93.84% | 97.26% | 48 / 11 |
| temporal_L5_v0.8,1.0,1.2_lambda1 | 89.73% | 97.95% | 99.32% | 64 / 12 |
| temporal_L9_v0.8,1.0,1.2_lambda1 | 97.26% | 100.00% | 100.00% | 78 / 4 |

The 90 methods per split include all 80 L/velocity-set/weight combinations, seven single/static baselines, and three shuffled controls. No configuration deleted. Best fixed temporal uses L=9, velocity=1.2, lambda=1 selected on validation with the predeclared deterministic tie rule. It yields 291/292 versus A 210/292; 82 rescues and one harm. The full three-velocity L9 baseline is 284/292 versus shuffled history 238/292. This supports an order-dependent effect without making an independent generalization claim.

Actual 18 development-image replays have exact descriptor agreement with cached rows; CPU/GPU float64 cosine scores agree within declared 1e-12 and top-10 ranks agree; causal L9 replay ranking agrees. First attempt omitted process-local TORCH_HOME and was interrupted during redundant initializer download; SIGINT/failed logs retained unchanged. Retry changed only cache location, not encoders or search protocol. No real latency results claimed here.

All 49 original/V2 tests pass. Actual manifest reordering retains identical ID-to-label alignment; 540 metric cells independently recounted from 81,000 per-query rows. Figure point CSV records exact numerators, denominators and input SHA.

Decision: research track A only. Near-ceiling fixed baseline leaves one validation error, so an adaptive advantage is not assumed. G3 gets one fixed concrete rule with prescribed ablations; if it does not beat fixed temporal, freeze an empirical interpretation and stop adding mechanisms. No expansion to fusion track B while temporal signal is positive.
