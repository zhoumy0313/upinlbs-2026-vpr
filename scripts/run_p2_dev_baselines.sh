#!/usr/bin/env bash
# Source-pinned development-only baseline; stages are sequential for timing.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
P2_RUN="$(mktemp -d "$ROOT/outputs/p2_recheck_$(date +%Y%m%d_%H%M%S)_XXXXXX")"
P2_MANIFEST="$ROOT/outputs/p1_20261010_132030/nordland_manifest_v2.json"
export PYTHONPATH=
export PYTHONNOUSERSITE=1
export TORCH_HOME="$ROOT/weights/p0_torch"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
record() {
    local command_name="$1"
    shift
    python3 scripts/record_command.py --run-dir "$P2_RUN" --name "$command_name" --cwd "$ROOT" \
        --env PYTHONPATH= --env PYTHONNOUSERSITE=1 --env TORCH_HOME="$TORCH_HOME" \
        --env OMP_NUM_THREADS=4 --env MKL_NUM_THREADS=4 --env OPENBLAS_NUM_THREADS=4 -- "$@"
}
cp configs/protocol.yaml "$P2_RUN/protocol.yaml"
cp configs/model_sources.json "$P2_RUN/model_sources.json"
cp "$P2_MANIFEST" "$P2_RUN/nordland_manifest.json"
record source_snapshot .venv-p0/bin/python scripts/snapshot_research_state.py --output "$P2_RUN/source_snapshot.json"
record unit_tests .venv-p0/bin/python -m pytest -q
record encoder_probe .venv-p0/bin/python scripts/probe_frozen_encoders.py --manifest "$P2_MANIFEST" --run-dir "$P2_RUN"
for encoder_name in cosplace dinov2; do
    record "extract_$encoder_name" .venv-p0/bin/python scripts/extract_dev_descriptors.py \
        --manifest "$P2_MANIFEST" --method "$encoder_name" --run-dir "$P2_RUN"
done
record evaluate_dev .venv-p0/bin/python scripts/evaluate_dev_baselines.py --manifest "$P2_MANIFEST" --run-dir "$P2_RUN"
record matching_examples .venv-p0/bin/python scripts/plot_dev_matching_examples.py --manifest "$P2_MANIFEST" --run-dir "$P2_RUN"
record real_latency .venv-p0/bin/python scripts/benchmark_dev_encoders.py --manifest "$P2_MANIFEST" --run-dir "$P2_RUN"
record dependencies .venv-p0/bin/python -m pip check
printf '%s\n' "$P2_RUN"
