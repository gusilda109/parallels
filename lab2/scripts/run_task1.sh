#!/usr/bin/env bash
# scripts/run_task1.sh — замеры Задания 1.
# Замеряет mat-vec на N=20000 и N=40000 для 1..40 потоков, по 5 повторов
# (берётся минимум). Результат — results/task1.csv.
#
# Использование:
#   ./scripts/run_task1.sh [REPEATS]

set -euo pipefail

REPEATS=${1:-5}
THREADS_LIST=(1 2 4 7 8 16 20 40)
SIZES=(20000 40000)

OUT=results/task1.csv
mkdir -p results
echo "N,threads,time_s" > "$OUT"

for N in "${SIZES[@]}"; do
    for th in "${THREADS_LIST[@]}"; do
        line=$(OMP_NUM_THREADS="$th" OMP_PROC_BIND=close OMP_PLACES=cores \
               ./bin/task1_matvec "$N" "$REPEATS")
        echo "[N=$N th=$th] $line"
        t=$(echo "$line" | sed -nE 's/.*best_time=([0-9.]+).*/\1/p')
        echo "$N,$th,$t" >> "$OUT"
    done
done

echo
echo "Done. Results in $OUT"
if command -v column >/dev/null 2>&1; then
    column -s, -t < "$OUT"
else
    cat "$OUT"
fi
