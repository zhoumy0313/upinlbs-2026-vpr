# G1 diagnosis — development only

Run `g1_diagnosis_20261010T131552Z_19ac45fe`; metrics SHA `28a67978719df33d140c91bacf1b46a8c3eb871ba10a589c83b1c42387f23e90`. Radius ±5 ordinal frames; unchanged gallery of 1750.

| Split / method | R@1 | R@5 | R@10 | R@20 | R@50 |
|---|---:|---:|---:|---:|---:|
| train / cosplace | 82.50% | 94.00% | 96.67% | 98.67% | 99.67% |
| train / eigenplaces | 86.67% | 96.83% | 98.33% | 99.50% | 100.00% |
| train / dinov2 | 46.67% | 69.67% | 77.67% | 85.33% | 93.33% |
| train / A+B union oracle (diagnostic only) | 92.33% | 98.50% | 100.00% | 100.00% | 100.00% |
| validation / cosplace | 71.33% | 92.00% | 97.33% | 98.33% | 100.00% |
| validation / eigenplaces | 83.33% | 94.33% | 96.67% | 97.67% | 99.67% |
| validation / dinov2 | 51.67% | 75.67% | 83.00% | 90.67% | 96.33% |
| validation / A+B union oracle (diagnostic only) | 88.33% | 98.00% | 99.67% | 100.00% | 100.00% |

CosPlace train: 103/600 rank errors with a positive in Top-50, 2/600 missing; validation: 86/300 rank errors and 0/300 missing. GT-supported recent Top-50 candidates are only an offline possibility diagnostic (100 train, 85 validation), never inference features or demonstrated temporal rescues.

All 4100 existing dataset images rehashed and decoded. Nordland raw names 251–2000 correspond to ordinal 1–1750; no train/validation exact duplicate bytes. Old test duplicate audit reproduces 79 groups / 187 records / 542 unique hashes. Visual examples show repeated railway/station structures and large seasonal changes; visual or byte evidence does not prove precise pose or a unique causal explanation for the old accuracy drop. Primary frame tolerance unchanged. GP GThard identity and GTsoft ignore semantics read in original loader/metric code.

Development examples are in the run figures directory; public examples.json contains only IDs/ranks and regenerate instructions: run_g1.py recreates panels from licensed local images. Old descriptive station example: outputs/p4_frozen_20261010_152754_Z1p6iu/figures_readable_v3/example_nordland_both_wrong.png. No old-test retrieval was recomputed here.

Primary literature matrix: RELATED_WORK_MATRIX.md. SMR already addresses trusting temporal matches; adaptive blending is a hypothesis, not an established novelty. Two original papers have metadata/author-follow-up access only, with real HTTP 202/404 records; no unverified equations or scores are attributed to them.

St Lucia official rsync listing is accessible: 3016 regular files, 123,494,841 bytes (~0.123 GB), below the 30 GB cap. Metadata filenames contain UTM zone and traversal/frame IDs, but chronology/segment/GT/licence suitability still requires G4 audit. No data/descriptor performance opened; alternate dataset unused.

Decision: advance to G2 with the grid recorded in this acceptance run before measuring it. All models will share an 8-frame warmup exclusion for main comparisons; full-stream startup will be reported separately.
