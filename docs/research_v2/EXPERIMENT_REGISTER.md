# Experiment register

| Stage | Hypothesis/task | Data role | Run | Status |
|---|---|---|---|---|
| G0 | Preserve V1 and verify environment/tests | no new retrieval experiment | g0_preserve_20261010T130954Z_842e31e4 | in progress |
| G0 | Preservation/regression after ROS plugin isolation | metadata only | g0_regression_20261010T131233Z_697c38c9 | passed, 34 tests |
| G1 | GT/order + candidate diagnosis | train/validation only; old test descriptive | g1_diagnosis_20261010T131552Z_19ac45fe / g1_acceptance_20261010T132758Z_bd97657b | passed with text-access limitations |
| G2 | Fixed causal temporal/fusion finite grid | train/validation | g2_strong_baselines_20261010T133356Z_5d8c3f15 / g2_acceptance_20261010T133813Z_d6200bfc | passed, track A |
| G3 | One adaptive rule, ablations, SMR first-filter adaptation | train/val | g3_adaptive_development_20261010T134356Z_93dbfee7; g3_smr_adaptation_20261010T135720Z_bcbbf327; g3_acceptance_20261010T140208Z_5ab06d53 | scientifically_negative |
| G4 | Frozen St Lucia + true batch1 timing | independent | g4_independent_evaluation_20261010T143959Z_73e61bb4;g4_real_online_latency_20261010T144339Z_bb8f86bb;g4_acceptance_20261010T150725Z_c4fe2906 | Outcome B |

Current qualification: G0 initial ROS test failure preserved; later G0 accepted. G4 overall C, original primary25m B retained. G5 g5_final_delivery_20261010T155038Z_3d2f7c92 passed after g5_delivery_verification_20261010T154422Z_56bc2592 and visual checks; five manuscript versions, negative adaptive and radius reversal retained. Full append-only run register in final archive.
