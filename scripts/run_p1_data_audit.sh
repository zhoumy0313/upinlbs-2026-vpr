#!/usr/bin/env bash
# Append-only P1 reproduction. Raw pair inspection and gallery self-checks only.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
P1_RUN="$(mktemp -d "$ROOT/outputs/p1_recheck_$(date +%Y%m%d_%H%M%S)_XXXXXX")"
export PYTHONPATH=
export PYTHONNOUSERSITE=1
export TORCH_HOME="$ROOT/weights/p0_torch"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
record() {
    local command_name="$1"
    shift
    python3 scripts/record_command.py --run-dir "$P1_RUN" --name "$command_name" --cwd "$ROOT" \
        --env PYTHONPATH= --env PYTHONNOUSERSITE=1 --env TORCH_HOME="$TORCH_HOME" \
        --env OMP_NUM_THREADS=4 --env MKL_NUM_THREADS=4 -- "$@"
}
cp configs/protocol.yaml "$P1_RUN/protocol.yaml"
record source_snapshot .venv-p0/bin/python scripts/snapshot_research_state.py --output "$P1_RUN/source_snapshot.json"
record unit_tests .venv-p0/bin/python -m pytest -q
if [[ ! -f data/downloads/GardensPoint_Walking.zip ]]; then
    mkdir -p data/downloads
    record download_gardens curl --fail --location --retry 3 --output data/downloads/GardensPoint_Walking.zip \
        https://www.tu-chemnitz.de/etit/proaut/datasets/GardensPoint_Walking.zip
fi
record verify_or_download_nordland .venv-p0/bin/python scripts/download_nordland_ranges.py
for dataset_name in gardens_point nordland; do
    record "prepare_$dataset_name" .venv-p0/bin/python scripts/prepare_data.py \
        --dataset "$dataset_name" --run-dir "$P1_RUN"
    sample_limit=0
    if [[ "$dataset_name" == nordland ]]; then sample_limit=64; fi
    record "self_$dataset_name" .venv-p0/bin/python scripts/check_gallery_self_retrieval.py \
        --dataset "$dataset_name" --manifest "$P1_RUN/${dataset_name}_manifest_v2.json" \
        --run-dir "$P1_RUN" --limit "$sample_limit"
    record "alignment_$dataset_name" .venv-p0/bin/python scripts/plot_alignment_examples.py \
        --manifest "$P1_RUN/${dataset_name}_manifest_v2.json" \
        --output "$P1_RUN/${dataset_name}_alignment.jpg"
done
record dependencies .venv-p0/bin/python -m pip check
record dependency_lock .venv-p0/bin/python -m pip freeze
printf '%s\n' "$P1_RUN"
