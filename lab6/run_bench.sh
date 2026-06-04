#!/usr/bin/env bash

set -u

TOL=${TOL:-1e-6}
ITERS=${ITERS:-1000000}
CSV=results.csv

echo "target,grid,iters,error,time" > "$CSV"

run() {
    local target="$1" bin="$2" g="$3"
    [ -x "$bin" ] || { echo "  пропуск: нет $bin"; return; }
    echo ">> $target  grid=$g"
    local out
    out=$(./"$bin" --grid "$g" --tol "$TOL" --iters "$ITERS")
    echo "$out"
    local it er tm
    it=$(echo "$out" | awk -F: '/Iterations/{gsub(/ /,"",$2);print $2}')
    er=$(echo "$out" | awk -F: '/Error/{gsub(/ /,"",$2);print $2}')
    tm=$(echo "$out" | awk -F: '/Time/{gsub(/ /,"",$2);print $2}')
    echo "$target,$g,$it,$er,$tm" >> "$CSV"
}

for g in 128 256 512; do run "cpu_onecore" heat_host "$g"; done

echo "ACC_NUM_CORES=${ACC_NUM_CORES:-<все>}"
for g in 128 256 512 1024; do run "cpu_multicore" heat_multicore "$g"; done

for g in 128 256 512 1024; do run "gpu" heat_gpu "$g"; done

echo
echo "Готово. Таблица: $CSV"
column -s, -t "$CSV"