#!/bin/bash
# Copy the code, data and current judge cache to /tmp on the node (home is at
# quota) and start the Llama cache fill there, detached from this session.
set -euo pipefail
cd "$(dirname "$0")/../.."

ssh -o BatchMode=yes uc-cluster "mkdir -p /tmp/lexflip_baralgb/results/llm_cache"
rsync -a --exclude '__pycache__' src data uc-cluster:/tmp/lexflip_baralgb/
rsync -a results/exp4_challenge.json results/paraphrases.jsonl uc-cluster:/tmp/lexflip_baralgb/results/
rsync -a results/llm_cache/ uc-cluster:/tmp/lexflip_baralgb/results/llm_cache/
ssh -o BatchMode=yes -n uc-cluster 'cd /tmp/lexflip_baralgb && (JUDGE_WORKERS=64 setsid nohup ~/jupyter-env/bin/python src/cluster/fill_llama_cache.py > fill.log 2>&1 < /dev/null &); sleep 3; tail -2 fill.log'
