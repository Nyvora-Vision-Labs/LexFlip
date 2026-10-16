#!/bin/bash
# Everything that needs the second judge (Llama-3.3-70B on the cluster, via the
# SSH tunnel on :8010), in dependency order. Every step is cached and resumable.
set -euo pipefail
cd "$(dirname "$0")"
export JUDGE_WORKERS=64 JUDGE_BUDGET_USD=4
F='torchao|redirects'
echo "== paraphrases";  python3 gen_paraphrases.py 2>&1 | grep -v -E "$F"
echo "== judge controls (llama)"; JUDGES=meta-llama/Llama-3.3-70B-Instruct python3 exp10_judge_controls.py 2>&1 | grep -v -E "$F"
echo "== specificity (metrics + both judges)"; METRICS_DEVICE=cpu python3 exp8_specificity.py 2>&1 | grep -v -E "$F|Loading|LOAD|UNEXPECTED|MISSING|Notes|pred_layer|can be ignored|^-|^$"
echo "== audit sheet"; python3 make_audit_sheet.py 2>&1 | grep -v -E "$F"
echo "== done"
