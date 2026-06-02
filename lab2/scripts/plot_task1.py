#!/usr/bin/env python3
"""scripts/plot_task1.py — график ускорения для Задания 1.

Читает results/task1.csv (формат: N,threads,time_s) и строит график:
по оси X — число потоков, по оси Y — ускорение S(p)=T(1)/T(p),
по одной кривой на размер задачи (N=20000 и N=40000), плюс линия Linear.
Сохраняет в results/task1_speedup.png.
"""
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV  = ROOT / "results" / "task1.csv"

by_N = defaultdict(list)   # N -> list of (threads, time_s)
with CSV.open() as f:
    for row in csv.DictReader(f):
        by_N[int(row["N"])].append((int(row["threads"]), float(row["time_s"])))

fig, ax = plt.subplots(figsize=(7, 5))
max_p = max(t for rows in by_N.values() for t, _ in rows)
ax.plot([1, max_p], [1, max_p], ls="--", color="gray", label="Linear")

print(f"{'N':>6} | {'p':>3} {'T(p), s':>9} {'S(p)':>6} {'E(p)':>6}")
print("-" * 40)
for N in sorted(by_N.keys()):
    rows = sorted(by_N[N], key=lambda r: r[0])
    T1 = next(t for p, t in rows if p == 1)
    xs = [p for p, _ in rows]
    ys = [T1 / t for _, t in rows]
    ax.plot(xs, ys, marker="o", label=f"N = {N}")
    for p, t in rows:
        s = T1 / t
        print(f"{N:>6} | {p:>3} {t:>9.4f} {s:>6.2f} {s/p:>6.2f}")

ax.set_xlabel("Число потоков p")
ax.set_ylabel("Ускорение S(p)")
ax.set_title("Задание 1: ускорение умножения матрицы на вектор")
ax.grid(True, ls=":")
ax.legend()
fig.tight_layout()
out = ROOT / "results" / "task1_speedup.png"
fig.savefig(out, dpi=140)
print(f"\nГрафик: {out}")
