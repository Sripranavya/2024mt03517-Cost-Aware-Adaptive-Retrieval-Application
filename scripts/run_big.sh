#!/usr/bin/env bash
# Larger HotpotQA test: n=200 (the first 80 are the earlier test questions, by hash order).
# No tuning here: cost weight 40 was chosen on validation (results/hpv2/chosen_cost_weight.txt)
# and STALE_PATIENCE stays off, exactly as in the reported v2 run. A fresh index is built
# (hp-t200, about 2,000 passages, so the distractor pool is larger than the n=80 index).
#
#   bash ~/scripts/run_big.sh
set -u
cd "$(dirname "$0")/../backend" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate

export LIVE_SOURCES=false SEED_SAMPLE_CORPUS=false MAX_BUDGET_USD="${MAX_BUDGET_USD:-12}"
export REWARD_COST_WEIGHT="$(cat results/hpv2/chosen_cost_weight.txt)"
export OPENSEARCH_INDEX=hp-t200
N="${N:-200}"
WORKERS="${WORKERS:-3}"
out=results/hpv4/test"$N"
mkdir -p "$out"

if [ -f "$out/benchmark_test.csv" ]; then
  echo "[skip] test n=$N"
else
  echo "[run ] test n=$N cost_weight=$REWARD_COST_WEIGHT  $(date +%T)"
  python ../scripts/run_benchmark.py --dataset hotpotqa --split test --max-per-split "$N" \
    --strategies pomdp fixed fixed_2 --reuse-index --workers "$WORKERS" --out "$out" \
    || { echo "[FAIL] test n=$N"; exit 1; }
fi

{
  echo "== hotpotqa test n=$N (cost_weight=$REWARD_COST_WEIGHT, stale off)"
  cut -d, -f2-12 "$out/benchmark_test.csv"
  python ../scripts/significance.py "$out/benchmark_test_per_query.csv"
  python ../scripts/frontier.py "$out"
} > "$out/summary.txt" 2>&1
cat "$out/summary.txt"
echo "ALL DONE $(date +%T)"
