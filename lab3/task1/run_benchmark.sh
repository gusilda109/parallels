#!/usr/bin/env bash
# Прогон бенчмарка Task 1 для всех требуемых размеров и числа потоков.
# Результаты пишутся в results.csv (формат: N,threads,time_seconds).
#
# По заданию: потоки 1,2,4,7,8,16,20,40; матрицы 20000 и 40000.
# Внимание: 40000x40000 double ~ 12 GiB ОЗУ — запускать на сервере.
#
# Usage:
#   ./run_benchmark.sh           # без привязки потоков
#   ./run_benchmark.sh pin       # с привязкой к ядрам (affinity)

set -euo pipefail

BIN=./matvec
PIN_ARG="${1:-}"          # "" или "pin"
OUT="results${PIN_ARG:+_pin}.csv"

THREADS=(1 2 4 7 8 16 20 40)
SIZES=(20000 40000)
REPEAT=3                   # число повторов; берём минимальное время

echo "N,threads,time_seconds" > "$OUT"

for N in "${SIZES[@]}"; do
  for T in "${THREADS[@]}"; do
    best=""
    for ((r=0; r<REPEAT; r++)); do
      line=$("$BIN" "$N" "$T" $PIN_ARG)      # "N,threads,time"
      tval=$(echo "$line" | cut -d',' -f3)
      if [[ -z "$best" ]] || awk "BEGIN{exit !($tval < $best)}"; then
        best="$tval"
      fi
    done
    echo "$N,$T,$best" | tee -a "$OUT"
  done
done

echo "Done. Results -> $OUT"
