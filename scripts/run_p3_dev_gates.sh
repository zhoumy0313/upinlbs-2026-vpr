#!/usr/bin/env bash
# Build fresh development caches and measure actual causal routing sequentially.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
P3_SECOND="${1:-eigenplaces}"
case "$P3_SECOND" in dinov2|eigenplaces) ;; *) exit 2 ;; esac
P3_RUN="$(mktemp -d "$ROOT/outputs/p3_${P3_SECOND}_$(date +%Y%m%d_%H%M%S)_XXXXXX")"
P3_MANIFEST="$ROOT/data/manifests/p1_20261010_132030_nordland_manifest_v2.json"
export PYTHONPATH= PYTHONNOUSERSITE=1
export TORCH_HOME="$ROOT/weights/p0_torch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
record() {
    local command_name="$1"
    shift
    python3 scripts/record_command.py --run-dir "$P3_RUN" --name "$command_name" --cwd "$ROOT" \
        --env PYTHONPATH= --env PYTHONNOUSERSITE=1 --env TORCH_HOME="$TORCH_HOME" \
        --env OMP_NUM_THREADS=4 --env MKL_NUM_THREADS=4 --env OPENBLAS_NUM_THREADS=4 -- "$@"
}
cp configs/protocol.yaml "$P3_RUN/protocol.yaml"
cp configs/model_sources.json "$P3_RUN/model_sources.json"
cp "$P3_MANIFEST" "$P3_RUN/nordland_manifest.json"
if [ "$P3_SECOND" = eigenplaces ]; then
    cp outputs/p3_dinov2_stable_20261010_141000/fallback_decision.json "$P3_RUN/fallback_decision.json"
fi
printf '%s\n' "$P3_RUN"
record source_snapshot .venv-p0/bin/python scripts/snapshot_research_state.py --output "$P3_RUN/source_snapshot.json"
record unit_tests .venv-p0/bin/python -m pytest -q
record encoder_probe .venv-p0/bin/python scripts/probe_frozen_encoders.py --manifest "$P3_MANIFEST" --run-dir "$P3_RUN" --methods cosplace "$P3_SECOND"
for encoder_name in cosplace "$P3_SECOND"; do
    record "extract_$encoder_name" .venv-p0/bin/python scripts/extract_dev_descriptors.py --manifest "$P3_MANIFEST" --method "$encoder_name" --run-dir "$P3_RUN"
done
record evaluate_dev .venv-p0/bin/python scripts/evaluate_dev_baselines.py --manifest "$P3_MANIFEST" --run-dir "$P3_RUN" --second-method "$P3_SECOND"
record matching_examples .venv-p0/bin/python scripts/plot_dev_matching_examples.py --manifest "$P3_MANIFEST" --run-dir "$P3_RUN"
record fit_evaluate_gates .venv-p0/bin/python scripts/fit_evaluate_dev_gates.py --feature-run "$P3_RUN" --manifest "$P3_MANIFEST" --run-dir "$P3_RUN" --second-method "$P3_SECOND"
record causal_consistency .venv-p0/bin/python scripts/verify_causal_gate_consistency.py --feature-run "$P3_RUN" --manifest "$P3_MANIFEST" --run-dir "$P3_RUN"
record online_validation_budget25 .venv-p0/bin/python scripts/benchmark_dev_routing.py --feature-run "$P3_RUN" --manifest "$P3_MANIFEST" --run-dir "$P3_RUN" --budget 25
record dependencies .venv-p0/bin/python -m pip check
printf '%s\n' "$P3_RUN"
