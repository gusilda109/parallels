#!/usr/bin/env bash
# scripts/run_schedule.sh — исследование параметров schedule().
# Фиксируем N и число потоков, перебираем static/dynamic/guided/auto
# и значения chunk. Результат — results/schedule.csv .
#
# Использование:
#   ./scripts/run_schedule.sh [N] [THREADS] [REPEATS]

set -euo pipefail

N=${1:-15000}
THREADS=${2:-8}
REPEATS=${3:-3}

SCHEDULES=("static 0" "static 1" "dynamic 0" "dynamic 1" "guided 0" "auto 0")

OUT=results/schedule.csv
mkdir -p results
echo "version,schedule,chunk,threads,N,iters,time_s" > "$OUT"

run_one() {
    local bin="$1"; local label="$2"; local sch="$3"; local chunk="$4"
    local best=""
    for r in $(seq 1 "$REPEATS"); do
        local line
        line=$(OMP_NUM_THREADS="$THREADS" OMP_PROC_BIND=close OMP_PLACES=cores \
               "$bin" "$N" "$sch" "$chunk")
        echo "[$label sch=$sch chunk=$chunk rep=$r] $line"
        local t
        t=$(echo "$line" | sed -nE 's/.*time=([0-9.]+).*/\1/p')
        if [[ -z "$best" || $(echo "$t < $best" | bc -l) -eq 1 ]]; then
            best="$t"
            iters=$(echo "$line" | sed -nE 's/.*iters=([0-9]+).*/\1/p')
        fi
    done
    echo "$label,$sch,$chunk,$THREADS,$N,$iters,$best" >> "$OUT"
}

for combo in "${SCHEDULES[@]}"; do
    sch="${combo% *}"
    chunk="${combo##* }"
    run_one ./bin/parallel_v1 v1 "$sch" "$chunk"
    run_one ./bin/parallel_v2 v2 "$sch" "$chunk"
done

echo
echo "Done. Results in $OUT"
if command -v column >/dev/null 2>&1; then
    column -s, -t < "$OUT"
else
    cat "$OUT"
fi
