#!/usr/bin/env python3
"""scripts/plot_task2.py — график ускорения для Задания 2."""
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

fig, ax = plt.subplots(figsize=(8, 5.5))
max_p = max(p for p, _ in rows)
ax.plot([1, max_p], [1, max_p], ls="--", color="gray",
        alpha=0.7, label="Идеальное (линейное)")

xs = [p for p, _ in rows]
ys = [T1 / t for _, t in rows]
color = "tab:orange"
ax.plot(xs, ys, marker="o", color=color, label="integrate_omp")

# Подсветка максимума
imax = ys.index(max(ys))
ax.scatter([xs[imax]], [ys[imax]], s=200, facecolor="none",
           edgecolor=color, linewidth=2.5, zorder=5)
ax.annotate(f"max: p={xs[imax]}, S={ys[imax]:.1f}×",
            xy=(xs[imax], ys[imax]), xytext=(8, -22),
            textcoords="offset points", fontsize=9, color=color,
            arrowprops=dict(arrowstyle="->", color=color, lw=1))

ax.set_xlabel("Число потоков p")
ax.set_ylabel("Ускорение S(p) = T(1)/T(p)")
ax.set_title("Задание 2. Ускорение численного интегрирования\n(круг — точка максимального ускорения)")
ax.set_xticks([1,2,4,7,8,16,20,40])
ax.grid(True, ls=":", alpha=0.6)
ax.legend(loc="upper left")
fig.tight_layout()
out = ROOT / "results" / "task2_speedup.png"
fig.savefig(out, dpi=140)

print(f"{'p':>3} {'T(p), s':>9} {'S(p)':>6} {'E(p)':>6}")
print("-" * 32)
for p, t in rows:
    s = T1 / t
    print(f"{p:>3} {t:>9.4f} {s:>6.2f} {s/p:>6.2f}")
print(f"\nГрафик: {out}")
