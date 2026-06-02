#!/usr/bin/env python3
"""scripts/plot_task2.py — график ускорения для Задания 2.

Читает results/task2.csv (формат: threads,nsteps,time_s) и строит график:
ускорение S(p) = T(1)/T(p) в зависимости от числа потоков.
Сохраняет в results/task2_speedup.png.
"""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV  = ROOT / "results" / "task2.csv"

rows = []
with CSV.open() as f:
    for r in csv.DictReader(f):
        rows.append((int(r["threads"]), float(r["time_s"])))
rows.sort()
T1 = next(t for p, t in rows if p == 1)

fig, ax = plt.subplots(figsize=(7, 5))
max_p = max(p for p, _ in rows)
ax.plot([1, max_p], [1, max_p], ls="--", color="gray", label="Linear")

xs = [p for p, _ in rows]
ys = [T1 / t for _, t in rows]
ax.plot(xs, ys, marker="o", color="C1", label="integrate_omp")

ax.set_xlabel("Число потоков p")
ax.set_ylabel("Ускорение S(p)")
ax.set_title("Задание 2: ускорение численного интегрирования")
ax.grid(True, ls=":")
ax.legend()
fig.tight_layout()
out = ROOT / "results" / "task2_speedup.png"
fig.savefig(out, dpi=140)

print(f"{'p':>3} {'T(p), s':>9} {'S(p)':>6} {'E(p)':>6}")
print("-" * 32)
for p, t in rows:
    s = T1 / t
    print(f"{p:>3} {t:>9.4f} {s:>6.2f} {s/p:>6.2f}")
print(f"\nГрафик: {out}")
