#!/usr/bin/env bash
# Ablation: full cost-based POMDP vs the quality-only POMDP on the test split.
# Fixed-depth and heuristic-routing variants are `fixed`/`adaptive` in the main test run.
# Uses the cost weight already chosen on validation by run_all.sh.
#
#   RUN_TAG=v2 DATASETS="hotpotqa msmarco" bash ~/scripts/run_ablation.sh
set -u
cd "$(dirname "$0")/../backend" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate

export LIVE_SOURCES=false SEED_SAMPLE_CORPUS=false
export MAX_BUDGET_USD="${MAX_BUDGET_USD:-30}"
DATASETS="${DATASETS:-hotpotqa}"
WORKERS="${WORKERS:-2}"
TEST_N="${TEST_N:-80}"

for ds in $DATASETS; do
  case "$ds" in hotpotqa) pfx=hp ;; musique) pfx=mq ;; *) pfx=ms ;; esac
  base="results/${pfx}${RUN_TAG:-}"
  out="$base/ablation"
  if [ ! -f "$base/chosen_cost_weight.txt" ]; then
    echo "[FAIL] $ds: run run_all.sh first ($base/chosen_cost_weight.txt missing)"
    continue
  fi
  cw="$(cat "$base/chosen_cost_weight.txt")"
  if [ -f "$out/benchmark_test.csv" ]; then
    echo "[skip] $ds ablation"
  else
    echo "[run ] $ds ablation (cost_weight=$cw)  $(date +%T)"
    REWARD_COST_WEIGHT="$cw" OPENSEARCH_INDEX="$pfx-test" \
      python ../scripts/run_benchmark.py --dataset "$ds" --split test \
      --max-per-split "$TEST_N" --strategies pomdp pomdp_quality \
      --reuse-index --workers "$WORKERS" --out "$out" || { echo "[FAIL] $ds ablation"; continue; }
  fi
  {
    echo "== $ds ablation (test): full cost-based POMDP vs quality-only"
    cut -d, -f2-12 "$out/benchmark_test.csv"
    python ../scripts/significance.py "$out/benchmark_test_per_query.csv"
  } > "$base/ablation_summary.txt" 2>&1
  echo "[done] $ds -> $base/ablation_summary.txt"
done
echo "ALL DONE $(date +%T)"
