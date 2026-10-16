#!/bin/bash
# exp3b grid, one process per (config, vary, seed) because MPS does not
# reliably release memory between runs inside one process. Resumable: the
# script skips any (config, vary, seed) already in results/exp3b_indist.json.
set -u
cd "$(dirname "$0")"
for spec in "scalar both" "da both" "da+edit both" "scalar split" "scalar init"; do
  set -- $spec
  for sd in 42 43 44 45 46; do
    python3 exp3b_indist.py --config "$1" --vary "$2" --seeds "$sd" 2>&1 | grep --line-buffered -v -E "torchao|redirects"
  done
done
