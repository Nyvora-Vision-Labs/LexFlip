#!/bin/bash
# Run the whole exp3b grid on ONE free GPU of the node (CUDA), after the vLLM
# judge server has been stopped. Output goes to results/exp3b_indist_cuda.json
# so it never mixes with the MPS runs made on the laptop.
#   on the node:  GPU=2 bash src/cluster/run_exp3b_cuda.sh
set -u
cd "$(dirname "$0")/../.."
export PYTHONPATH=/tmp/lexflip_pkgs HF_HOME=/tmp/hf_baralgb EXP3B_OUT=exp3b_indist_cuda.json
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=${GPU:-2}
PY=~/jupyter-env/bin/python
cd src
for spec in "scalar both" "da both" "da+edit both" "scalar split" "scalar init"; do
  set -- $spec
  for sd in 42 43 44 45 46; do
    $PY exp3b_indist.py --config "$1" --vary "$2" --seeds "$sd" 2>&1 | grep --line-buffered -E "^\[|Error|Traceback"
  done
done
echo "exp3b cuda grid done"
