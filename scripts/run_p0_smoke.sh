#!/usr/bin/env bash
# Reuse the prepared isolated environment; write a NEW run for every invocation.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
project_root="$PWD"
python_bin="$project_root/.venv-p0/bin/python"
repo_dir="$project_root/third_party/VPR-methods-evaluation"
test -x "$python_bin"
test -f "$repo_dir/main.py"
export PYTHONPATH=
export PYTHONNOUSERSITE=1
export TORCH_HOME="$project_root/weights/p0_torch"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
run_dir="$(mktemp -d "$project_root/outputs/p0_recheck_$(TZ=Asia/Shanghai date +%Y%m%d_%H%M%S)_XXXXXX")"
cp configs/protocol.yaml "$run_dir/protocol.yaml"
cp AGENTS.md PLAN.md "$run_dir/"
record=(python3 "$project_root/scripts/record_command.py" --run-dir "$run_dir"
  --env PYTHONPATH= --env PYTHONNOUSERSITE=1 --env TORCH_HOME="$TORCH_HOME"
  --env OMP_NUM_THREADS=4 --env MKL_NUM_THREADS=4)
"${record[@]}" --name environment -- python3 scripts/audit_environment.py
"${record[@]}" --name unit_tests -- "$python_bin" -m pytest -q --junitxml="$run_dir/unit_tests.xml"
device="$($python_bin -c 'import torch; print("cuda" if torch.cuda.is_available() else "cpu")')"
if [[ "$device" == cuda ]]; then
  "${record[@]}" --name gpu_probe -- "$python_bin" scripts/check_torch_gpu.py
fi
"${record[@]}" --name official_toy --cwd "$repo_dir" -- "$python_bin" main.py \
  --method=cosplace --backbone=ResNet18 --descriptors_dimension=512 \
  --database_folder=toy_dataset/database --queries_folder=toy_dataset/queries \
  --no_labels --image_size 200 200 --num_preds_to_save 3 \
  --device "$device" --batch_size 1 --num_workers 0 --save_descriptors \
  --log_dir "$run_dir/official_toy"
"${record[@]}" --name inspect_toy -- "$python_bin" scripts/inspect_toy_outputs.py --run-dir "$run_dir"
"${record[@]}" --name dependency_check -- "$python_bin" -m pip check
"${record[@]}" --name requirements_freeze -- "$python_bin" -m pip freeze
printf 'New smoke-test artifacts: %s\n' "$run_dir"
