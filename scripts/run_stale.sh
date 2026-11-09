#!/usr/bin/env bash
# Priority-1 experiment: stop after consecutive retrievals that return no new documents.
# Validation only (hp-val index, n=30). Rule fixed in advance: the smallest STALE_PATIENCE
# whose POMDP F1 stays within 0.02 of the STALE_PATIENCE=0 run (results/hpv2/val_cw40) and
# that cuts out-of-index spend. The test split is NOT touched here.
#
#   bash ~/scripts/run_stale.sh
set -u
cd "$(dirname "$0")/../backend" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate

export LIVE_SOURCES=false SEED_SAMPLE_CORPUS=false MAX_BUDGET_USD="${MAX_BUDGET_USD:-10}"
export REWARD_COST_WEIGHT=40 OPENSEARCH_INDEX=hp-val
WORKERS="${WORKERS:-3}"
VAL_N="${VAL_N:-30}"
out=results/hpv3
mkdir -p "$out"

for sp in 1 2; do
  d="$out/val_stale$sp"
  if [ -f "$d/benchmark_val.csv" ]; then
    echo "[skip] validation STALE_PATIENCE=$sp"
  else
    echo "[run ] validation all strategies STALE_PATIENCE=$sp  $(date +%T)"
    STALE_PATIENCE=$sp python ../scripts/run_benchmark.py --dataset hotpotqa --split val \
      --max-per-split "$VAL_N" --strategies pomdp fixed self_rag adaptive --reuse-index \
      --workers "$WORKERS" --out "$d" || { echo "[FAIL] validation $sp"; exit 1; }
  fi
done

for sp in 0 1 2; do
  f="$out/probe_stale$sp.txt"
  if [ -f "$f" ]; then
    echo "[skip] probe STALE_PATIENCE=$sp"
  else
    echo "[run ] out-of-index probe STALE_PATIENCE=$sp  $(date +%T)"
    STALE_PATIENCE=$sp python ../scripts/unanswerable_probe.py > "$f" 2>&1 \
      || { echo "[FAIL] probe $sp"; exit 1; }
  fi
done

{
  echo "== validation (n=$VAL_N, cost weight 40); STALE_PATIENCE=0 is results/hpv2"
  echo "setting,strategy,f1,avg_cost_usd,avg_hops"
  for sp in 0 1 2; do
    if [ "$sp" = 0 ]; then
      csvs="results/hpv2/val_cw40/benchmark_val.csv results/hpv2/val_baselines/benchmark_val.csv"
    else
      csvs="$out/val_stale$sp/benchmark_val.csv"
    fi
    for c in $csvs; do
      awk -F, -v s="stale$sp" 'NR>1 && $2=="all" {print s","$3","$7","$8","$10}' "$c"
    done
  done
  echo
  cat "$out"/probe_stale0.txt "$out"/probe_stale1.txt "$out"/probe_stale2.txt
} > "$out/summary.txt"
cat "$out/summary.txt"
echo "ALL DONE $(date +%T)"
