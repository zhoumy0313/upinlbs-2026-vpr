#!/usr/bin/env bash
# Final-test entry: exact package confirmation is checked before image access.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
P4_PACKAGE="${1:?Pass the approved freeze package selection.json}"
P4_RUN="$(mktemp -d "$ROOT/outputs/p4_frozen_$(date +%Y%m%d_%H%M%S)_XXXXXX")"
export PYTHONPATH= PYTHONNOUSERSITE=1
export TORCH_HOME="$ROOT/weights/p0_torch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
printf '%s\n' "$P4_RUN"
python3 scripts/record_command.py --run-dir "$P4_RUN" --name final_evaluation --cwd "$ROOT" \
    --env PYTHONPATH= --env PYTHONNOUSERSITE=1 --env TORCH_HOME="$TORCH_HOME" \
    --env OMP_NUM_THREADS=4 --env MKL_NUM_THREADS=4 --env OPENBLAS_NUM_THREADS=4 -- \
    .venv-p0/bin/python scripts/run_frozen_evaluation.py --package "$P4_PACKAGE" --output "$P4_RUN/results"
printf '%s\n' "$P4_RUN"
