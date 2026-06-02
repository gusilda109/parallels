#!/usr/bin/env python3
"""scripts/plot_task1.py — график ускорения для Задания 1.

Подсвечивает точку максимального ускорения для каждого N.
"""
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV  = ROOT / "results" / "task1.csv"

by_N = defaultdict(list)
with CSV.open() as f:
    for row in csv.DictReader(f):
        by_N[int(row["N"])].append((int(row["threads"]), float(row["time_s"])))

fig, ax = plt.subplots(figsize=(8, 5.5))
max_p = max(t for rows in by_N.values() for t, _ in rows)
ax.plot([1, max_p], [1, max_p], ls="--", color="gray",
        alpha=0.7, label="Идеальное (линейное)")

colors = ["tab:blue", "tab:orange", "tab:green"]
print(f"{'N':>6} | {'p':>3} {'T(p), s':>9} {'S(p)':>6} {'E(p)':>6}")
print("-" * 42)
for ci, N in enumerate(sorted(by_N.keys())):
    rows = sorted(by_N[N], key=lambda r: r[0])
    T1 = next(t for p, t in rows if p == 1)
    xs = [p for p, _ in rows]
    ys = [T1 / t for _, t in rows]
    color = colors[ci % len(colors)]
    ax.plot(xs, ys, marker="o", label=f"N = {N}", color=color)

    # Точка максимума
    imax = ys.index(max(ys))
    ax.scatter([xs[imax]], [ys[imax]], s=200, facecolor="none",
               edgecolor=color, linewidth=2.5, zorder=5)
    # разносим аннотации: первая (ci=0) — выше, вторая — ниже
    y_off = 25 if ci == 0 else -35
    ax.annotate(f"N={N}\nmax: p={xs[imax]}, S={ys[imax]:.1f}×",
                xy=(xs[imax], ys[imax]), xytext=(-95, y_off),
                textcoords="offset points", fontsize=9, color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=1))

    for p, t in rows:
        s = T1 / t
        print(f"{N:>6} | {p:>3} {t:>9.4f} {s:>6.2f} {s/p:>6.2f}")

ax.set_xlabel("Число потоков p")
ax.set_ylabel("Ускорение S(p) = T(1)/T(p)")
ax.set_title("Задание 1. Ускорение умножения матрицы на вектор\n(круг — точка максимального ускорения)")
ax.set_xticks([1,2,4,7,8,16,20,40])
ax.grid(True, ls=":", alpha=0.6)
ax.legend(loc="upper left")
fig.tight_layout()
out = ROOT / "results" / "task1_speedup.png"
fig.savefig(out, dpi=140)
print(f"\nГрафик: {out}")
