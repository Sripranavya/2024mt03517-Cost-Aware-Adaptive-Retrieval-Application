#!/usr/bin/env bash
# Resumable end-to-end benchmark for CloudShell (or any shell with AWS access).
#
# Per dataset: download -> validation sweep of the reward cost weight (POMDP only) ->
# baselines on validation -> pick the weight on validation only -> test split ->
# stopping study -> summary with confidence intervals and cost scenarios.
#
# Re-run after any interruption: steps whose output CSV exists are skipped.
#   nohup bash ~/scripts/run_all.sh > ~/run_all.log 2>&1 &
#   tail -5 ~/run_all.log
#
# Overrides (environment): DATASETS="hotpotqa musique" WORKERS=3 VAL_N=30 TEST_N=80
#                          STUDY_N=40 WEIGHTS="0.15 5 20 30 40 60" MAX_BUDGET_USD=30
set -u
cd "$(dirname "$0")/../backend" || exit 1
# shellcheck disable=SC1091
source .venv/bin/activate

export LIVE_SOURCES=false SEED_SAMPLE_CORPUS=false
export MAX_BUDGET_USD="${MAX_BUDGET_USD:-30}"
DATASETS="${DATASETS:-hotpotqa musique}"
WORKERS="${WORKERS:-3}"
VAL_N="${VAL_N:-30}"
TEST_N="${TEST_N:-80}"
STUDY_N="${STUDY_N:-40}"
WEIGHTS="${WEIGHTS:-0.15 5 20 30 40 60}"
BENCH=(python ../scripts/run_benchmark.py)

step() { # step <file that marks completion> <label> <command...>
  local marker="$1" label="$2"
  shift 2
  if [ -f "$marker" ]; then
    echo "[skip] $label"
    return 0
  fi
  echo "[run ] $label  $(date +%T)"
  "$@" || { echo "[FAIL] $label"; return 1; }
}

for ds in $DATASETS; do
  if [ "$ds" = hotpotqa ]; then pfx=hp; else pfx=mq; fi
  base="results/$pfx"
  mkdir -p "$base" data

  step "data/.done_$ds" "download $ds" \
    bash -c "${BENCH[*]} --dataset $ds --download-only && touch data/.done_$ds" || continue

  first=3
  for cw in $WEIGHTS; do
    out="$base/val_cw$cw"
    step "$out/benchmark_val.csv" "$ds validation pomdp cost_weight=$cw" \
      env REWARD_COST_WEIGHT="$cw" OPENSEARCH_INDEX="$pfx-val" \
      "${BENCH[@]}" --dataset "$ds" --split val --max-per-split "$VAL_N" \
      --strategies pomdp --reuse-index --workers "$WORKERS" --traces "$first" --out "$out" \
      || continue 2
    first=0
  done

  step "$base/val_baselines/benchmark_val.csv" "$ds validation baselines" \
    env OPENSEARCH_INDEX="$pfx-val" \
    "${BENCH[@]}" --dataset "$ds" --split val --max-per-split "$VAL_N" \
    --strategies fixed self_rag adaptive --reuse-index --workers "$WORKERS" \
    --out "$base/val_baselines" || continue

  step "$base/chosen_cost_weight.txt" "$ds pick cost weight (validation only)" \
    python ../scripts/pick_cost_weight.py "$base" || continue
  cw="$(cat "$base/chosen_cost_weight.txt")"

  step "$base/test/benchmark_test.csv" "$ds test split (cost_weight=$cw)" \
    env REWARD_COST_WEIGHT="$cw" OPENSEARCH_INDEX="$pfx-test" \
    "${BENCH[@]}" --dataset "$ds" --split test --max-per-split "$TEST_N" \
    --reuse-index --workers "$WORKERS" --out "$base/test" || continue

  step "$base/study/stopping_study.csv" "$ds stopping study (cost_weight=$cw)" \
    env REWARD_COST_WEIGHT="$cw" OPENSEARCH_INDEX="$pfx-study" \
    "${BENCH[@]}" --dataset "$ds" --split test --max-per-split "$STUDY_N" --study \
    --reuse-index --workers "$WORKERS" --out "$base/study" || continue

  {
    echo "== $ds test (cost_weight=$cw)"
    cat "$base/test/benchmark_test.csv"
    python ../scripts/significance.py "$base/test/benchmark_test_per_query.csv"
    python ../scripts/cost_sensitivity.py "$base/test/benchmark_test.csv" --prices 0 0.0005 0.002
    echo "== $ds stopping study"
    cat "$base/study/stopping_study.csv"
    python ../scripts/significance.py "$base/study/stopping_study_per_query.csv"
  } > "$base/summary.txt" 2>&1
  echo "[done] $ds -> $base/summary.txt"
done
echo "ALL DONE $(date +%T)"
