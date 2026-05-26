#!/usr/bin/env bash
# scripts/run_scaling.sh — замеры зависимости времени от числа потоков.
# Запускает serial, parallel_v1, parallel_v2 на каждом значении числа потоков.
# Результаты пишутся в results/scaling.csv .
#
# Использование:
#   ./scripts/run_scaling.sh [N] [REPEATS]
# По умолчанию N=15000, REPEATS=3 (берётся минимальное время из повторов).

set -euo pipefail

N=${1:-15000}
REPEATS=${2:-3}

THREADS_LIST=(1 2 4 7 8 16 20 40)

OUT=results/scaling.csv
mkdir -p results
echo "version,threads,N,iters,time_s,rel_res,err" > "$OUT"

run_and_log() {
    local bin="$1"; local label="$2"; local th="$3"
    local best="" line=""
    for r in $(seq 1 "$REPEATS"); do
        if [[ "$label" == "serial" ]]; then
            line=$("$bin" "$N")
        else
            line=$(OMP_NUM_THREADS="$th" OMP_PROC_BIND=close OMP_PLACES=cores "$bin" "$N")
        fi
        echo "[$label th=$th rep=$r] $line"
        # достаём time= из вывода
        local t
        t=$(echo "$line" | sed -nE 's/.*time=([0-9.]+).*/\1/p')
        if [[ -z "$best" || $(echo "$t < $best" | bc -l) -eq 1 ]]; then
            best="$t"
            # запоминаем строку с минимальным временем
            iters=$(echo  "$line" | sed -nE 's/.*iters=([0-9]+).*/\1/p')
            relres=$(echo "$line" | sed -nE 's/.*rel_res=([0-9.eE+-]+).*/\1/p')
            err=$(echo    "$line" | sed -nE 's/.*err=([0-9.eE+-]+).*/\1/p')
            # для serial у нас ||x-1||_inf
            [[ -z "$err" ]] && err=$(echo "$line" | sed -nE 's/.*\|\|x-1\|\|_inf=([0-9.eE+-]+).*/\1/p')
        fi
    done
    echo "$label,$th,$N,$iters,$best,$relres,$err" >> "$OUT"
}

echo "=== Serial baseline ==="
run_and_log ./bin/serial serial 1

echo "=== Parallel V1 ==="
for th in "${THREADS_LIST[@]}"; do
    run_and_log ./bin/parallel_v1 v1 "$th"
done

echo "=== Parallel V2 ==="
for th in "${THREADS_LIST[@]}"; do
    run_and_log ./bin/parallel_v2 v2 "$th"
done

echo
echo "Done. Results in $OUT"
if command -v column >/dev/null 2>&1; then
    column -s, -t < "$OUT"
else
    cat "$OUT"
fi
