#!/usr/bin/env bash
# scripts/run_task2.sh — замеры Задания 2 (численное интегрирование).
# nsteps = 40 000 000, потоки 1..40, 5 повторов (минимум).
# Результат — results/task2.csv.

set -euo pipefail

NSTEPS=${1:-40000000}
REPEATS=${2:-5}
THREADS_LIST=(1 2 4 7 8 16 20 40)

OUT=results/task2.csv
mkdir -p results
echo "threads,nsteps,time_s" > "$OUT"

for th in "${THREADS_LIST[@]}"; do
    line=$(OMP_NUM_THREADS="$th" OMP_PROC_BIND=close OMP_PLACES=cores \
           ./bin/task2_integrate "$NSTEPS" "$REPEATS")
    echo "[th=$th] $line"
    t=$(echo "$line" | sed -nE 's/.*best_time=([0-9.]+).*/\1/p')
    echo "$th,$NSTEPS,$t" >> "$OUT"
done

echo
echo "Done. Results in $OUT"
if command -v column >/dev/null 2>&1; then
    column -s, -t < "$OUT"
else
    cat "$OUT"
fi
