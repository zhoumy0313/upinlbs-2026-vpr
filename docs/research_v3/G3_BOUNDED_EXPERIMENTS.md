# G3 acceptance
1. Executed the declared finite 224-config grid: 32 P, 32 R1, 160 R2. R3 is the H=1 R1 alias, not an invented distinct algorithm.
2. Coarse T yields finite same-traversal candidates; P permits only candidates within epsilon of best T, then ranks by current S; remaining gallery completes by S. No GT or future input. Cache replay accelerates development only, not timing.
3. `.venv-p0/bin/python -m experiments.endpoint_vpr.run_g3`; CPU accuracy, 10 synthetic tests, per-query top10/candidates/eligible/paths/threshold sensitivities and raw outcomes preserved.
4. Selected P: P_fixed_L9_H3_r1_e0.06: 598/656 strict 10m. Strongest non-P: R2_full_L3_H3_r1_g0.75: 644/656. Net -46; 25m nondegradation=False; Nordland loss vs L9=6. Every H/r/gamma/epsilon combination and baseline shuffling/reverse history control remains available.
5. Identical split resets, masks, encoders and labels. St Lucia/Nordland validation are already seen; cannot claim blind generalization.
6. Predeclared development gate=False. Outcome C provisionally. No additional mechanism will be added after a negative P result. Novel contribution remains unsupported pending source and independent checks.
7. Broad oracle coverage does not guarantee usable performance; strict label uncertainty and high baseline ceiling remain.
8. Full per-query archive, hashes and selection timestamp; push receipt follows.
9. Next: complete independent-source access audit, then freeze the final comparison without opening new predictions.
