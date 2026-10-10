# AI implementation rules

## Scope
Work only in this project and the explicitly approved environment. Preserve
existing SSH/proxy/Codex settings. Do not install ROS, robot simulators, a CUDA
Toolkit, global Python packages or change GPU drivers without explaining why
and receiving approval. Audit actual hardware; never infer GPU/VRAM.

## Scientific constraints
1. No invented runs, numbers, citations, improvements or acceptance claims.
2. Read configs/protocol.yaml. All thresholds/model choices are train/validation
   decisions. Final-test labels are restricted to evaluation and audit scripts.
3. Gate inputs contain five A-only score statistics. No B descriptors, B scores,
   query ground-truth IDs/poses or correctness labels at online decision time.
4. This is supervised gate fitting with frozen encoders, NOT a training-free method.
5. Initial second stage is independent global B retrieval and rank replacement.
   Do not silently add fusion, sequence matching, reranking or geometric checks.
6. Retain failures. No deleting difficult images, widening tolerances after seeing
   results, changing seeds until improvement, or altering tests to hide defects.
7. Cache identity includes dataset/manifest hash, model+checkpoint hash, preprocessing,
   pooling, dimension, dtype and code version. Save image IDs with descriptor rows.
8. Cached-feature simulations are for accuracy experiments, not model latency.
9. Dataset GTsoft may be an ignore mask, not positives. Verify original code.
10. Experimental runs are append-only. Save command, config, commit, environment,
    per-query results, logs and metrics together. Never overwrite old runs.
11. Synthetic self-tests are not real VPR experiments. Label them explicitly.
12. Avoid redistributing image datasets/checkpoints; respect original licenses.
13. Do not store passwords, subscription URLs, authentication files or API keys
    in code, Git, prompts or logs. Do not collect them for debugging.
14. Before implementing a cited comparator, read its paper and code. State any
    adaptation. Never invent a metric from its name and label it official.
15. Do not submit a paper, agree to copyright terms, change authors, or pay fees.

## Delivery after every phase
- Changed files and one reproducible command.
- What actually ran; actual exit status; what did not run.
- Tests/results with artifact paths, not unsupported prose.
- 5--10 lines explaining input -> processing -> output to a DL beginner.
- Problems and the next single bounded task.
- No phase escalation beyond the requested scope.
