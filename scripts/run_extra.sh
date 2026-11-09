#!/usr/bin/env bash
# Benchmark the strategies that were never evaluated at scale (POMDP-VI, CRAG, FLARE,
# RAG-Fusion, Step-Back, HyDE) on the same HotpotQA test split as the headline run
# (hp-test index, n=80, cost weight 40, stale-stop off). POMDP and Fixed are re-run in the
# SAME process so paired confidence intervals compare like with like; Self-RAG and
# Adaptive-RAG numbers stay in results/hpv2/test (same split and index).
#
#   bash ~/scripts/run_extra.sh
set -u
cd "$(dirname "$0")/../backend" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate

export LIVE_SOURCES=false SEED_SAMPLE_CORPUS=false MAX_BUDGET_USD="${MAX_BUDGET_USD:-12}"
export REWARD_COST_WEIGHT="$(cat results/hpv2/chosen_cost_weight.txt)"
export OPENSEARCH_INDEX=hp-test
WORKERS="${WORKERS:-3}"
out=results/hpv5/extras
mkdir -p "$out"

if [ -f "$out/benchmark_test.csv" ]; then
  echo "[skip] extra strategies"
else
  echo "[run ] extra strategies n=80 cost_weight=$REWARD_COST_WEIGHT  $(date +%T)"
  python ../scripts/run_benchmark.py --dataset hotpotqa --split test --max-per-split 80 \
    --strategies pomdp fixed pomdp_vi crag flare rag_fusion step_back hyde \
    --reuse-index --workers "$WORKERS" --out "$out" || { echo "[FAIL] extras"; exit 1; }
fi

{
  echo "== extra strategies, hotpotqa test n=80 (cost_weight=$REWARD_COST_WEIGHT, stale off)"
  cut -d, -f2-12 "$out/benchmark_test.csv"
  echo "-- reference rows from results/hpv2/test (earlier run, same split and index)"
  cut -d, -f2-12 results/hpv2/test/benchmark_test.csv | grep -E "self_rag|adaptive"
  python ../scripts/significance.py "$out/benchmark_test_per_query.csv"
  python ../scripts/frontier.py "$out" results/hpv2/test
} > "$out/summary.txt" 2>&1
cat "$out/summary.txt"
echo "ALL DONE $(date +%T)"
