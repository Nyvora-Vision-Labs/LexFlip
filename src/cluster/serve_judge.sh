#!/usr/bin/env bash
# Serve the second judge family on ONE free GPU of the shared uc-cluster node,
# through vLLM's OpenAI-compatible server. The local experiment scripts reach
# it via an SSH tunnel on port 8010 (see src/llm_judge.py: LOCAL_ENDPOINT).
#
# The model is Llama-3.3-70B-Instruct in 4-bit AWQ, already in the HF cache on
# the node. (Qwen2.5-72B-Instruct-AWQ was the first choice; its download failed
# because the home-directory quota is full.)
#
#   usage on the cluster:  GPU=2 bash serve_judge.sh
#   tunnel from the laptop: ssh -N -L 8010:localhost:8010 uc-cluster
set -euo pipefail

GPU=${GPU:-2}
PORT=${PORT:-8010}
MODEL=casperhansen/llama-3.3-70b-instruct-awq
VENV=$HOME/naacl-agent-comm/.venv
LOG=$HOME/lexflip_judge

# The node has no scheduler; refuse to start on a GPU someone else took meanwhile.
used=$(nvidia-smi -i "$GPU" --query-gpu=memory.used --format=csv,noheader,nounits)
if [ "$used" -gt 2000 ]; then
  echo "GPU $GPU now has ${used} MiB in use; pick another free GPU." >&2
  exit 1
fi

# Home is at quota: keep compile caches on local disk and never download.
export PATH="$VENV/bin:$PATH"   # JIT kernels need the venv's ninja
export HF_HUB_OFFLINE=1
export VLLM_CACHE_ROOT=/tmp/vllm_cache_$USER
export TRITON_CACHE_DIR=/tmp/triton_cache_$USER
mkdir -p "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR"

# --served-model-name keeps the request name equal to the cache key the
# experiment scripts use, independent of the quantised checkpoint's repo id.
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$GPU exec "$VENV/bin/vllm" serve "$MODEL" \
  --served-model-name meta-llama/Llama-3.3-70B-Instruct \
  --quantization awq_marlin \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 64 \
  --port "$PORT" --host 127.0.0.1 \
  > "$LOG/vllm.log" 2>&1
