#!/usr/bin/env python3
"""scripts/plot.py — графики для Задания 3 (метод простой итерации).

Строит:
  - time.png       — время от числа потоков, с подсветкой оптимума
  - speedup.png    — ускорение с линейной отсечкой и подсветкой оптимума
  - efficiency.png — эффективность в виде столбцов (нагляднее линий),
                     с подсветкой границы 50% и оптимума
"""
from __future__ import annotations
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV  = ROOT / "results" / "scaling.csv"

def load():
    rows = []
    with CSV.open() as f:
        for row in csv.DictReader(f):
            row["threads"] = int(row["threads"])
            row["time_s"]  = float(row["time_s"])
            rows.append(row)
    return rows

def annotate_min(ax, xs, ys, color, label_prefix, y_offset=15):
    """Подсветить точку минимума (для time)."""
    imin = ys.index(min(ys))
    ax.scatter([xs[imin]], [ys[imin]], s=180, facecolor="none",
               edgecolor=color, linewidth=2.5, zorder=5)
    ax.annotate(f"{label_prefix} оптимум:\np={xs[imin]}, T={ys[imin]:.2f} с",
                xy=(xs[imin], ys[imin]), xytext=(-100, y_offset),
                textcoords="offset points", fontsize=9, color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=1))

def annotate_max(ax, xs, ys, color, label_prefix, y_offset=-25):
    """Подсветить точку максимума (для speedup)."""
    imax = ys.index(max(ys))
    ax.scatter([xs[imax]], [ys[imax]], s=180, facecolor="none",
               edgecolor=color, linewidth=2.5, zorder=5)
    ax.annotate(f"{label_prefix} оптимум:\np={xs[imax]}, S={ys[imax]:.1f}×",
                xy=(xs[imax], ys[imax]), xytext=(10, y_offset),
                textcoords="offset points", fontsize=9, color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=1))

def main():
    rows = load()
    serial = next(r for r in rows if r["version"] == "serial")
    T1 = serial["time_s"]
    print(f"Serial T(1) = {T1:.3f} s, N = {serial['N']}")

    versions = ["v1", "v2"]
    data = {v: sorted([r for r in rows if r["version"] == v],
                      key=lambda r: r["threads"]) for v in versions}
    colors = {"v1": "tab:blue", "v2": "tab:orange"}

    # ============ TIME ============
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.axhline(T1, ls="--", color="gray", alpha=0.7, label=f"Serial T(1)={T1:.1f}s")
    for i, v in enumerate(versions):
        xs = [r["threads"] for r in data[v]]
        ys = [r["time_s"]  for r in data[v]]
        ax.plot(xs, ys, marker="o", label=f"Variant {v.upper()}", color=colors[v])
        annotate_min(ax, xs, ys, colors[v], v.upper(),
                     y_offset=40 if i == 0 else 80)
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Время, с")
    ax.set_title("Время работы от числа потоков\n(круг — оптимальная точка)")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xticks([1,2,4,7,8,16,20,40])
    ax.set_xticklabels([1,2,4,7,8,16,20,40])
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "time.png", dpi=140)
    plt.close(fig)

    # ============ SPEEDUP ============
    fig, ax = plt.subplots(figsize=(8, 5.5))
    max_p = max(r["threads"] for v in versions for r in data[v])
    ax.plot([1, max_p], [1, max_p], ls="--", color="gray",
            alpha=0.7, label="Идеальное (линейное)")
    for i, v in enumerate(versions):
        xs = [r["threads"] for r in data[v]]
        ys = [T1 / r["time_s"] for r in data[v]]
        ax.plot(xs, ys, marker="o", label=f"Variant {v.upper()}", color=colors[v])
        annotate_max(ax, xs, ys, colors[v], v.upper(),
                     y_offset=-25 if i == 0 else 35)
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Ускорение S(p) = T(serial)/T(p)")
    ax.set_title("Ускорение распараллеливания\n(круг — точка максимума)")
    ax.set_xticks([1,2,4,7,8,16,20,40])
    ax.grid(True, ls=":", alpha=0.6)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "speedup.png", dpi=140)
    plt.close(fig)

    # ============ EFFICIENCY (столбцы) ============
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    threads_list = sorted({r["threads"] for v in versions for r in data[v]})
    x = list(range(len(threads_list)))
    width = 0.38

    eff = {v: [] for v in versions}
    for v in versions:
        by_p = {r["threads"]: T1 / r["time_s"] / r["threads"] for r in data[v]}
        eff[v] = [by_p.get(p, 0) for p in threads_list]

    bars_v1 = ax.bar([i - width/2 for i in x], eff["v1"], width,
                     label="V1", color=colors["v1"], alpha=0.85)
    bars_v2 = ax.bar([i + width/2 for i in x], eff["v2"], width,
                     label="V2", color=colors["v2"], alpha=0.85)

    # Подсветка оптимумов (макс эффективность среди p > 1)
    for v, bars in [("v1", bars_v1), ("v2", bars_v2)]:
        vals = eff[v]
        # игнорируем p=1 (там E≈1 по построению или ниже из-за оверхеда)
        idx_candidates = [i for i, p in enumerate(threads_list) if p > 1]
        if idx_candidates:
            best_i = max(idx_candidates, key=lambda i: vals[i])
            bars[best_i].set_edgecolor("red")
            bars[best_i].set_linewidth(2.5)

    # Подписи значений над столбцами
    for bars in (bars_v1, bars_v2):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h + 0.015, f"{h:.2f}",
                    ha="center", va="bottom", fontsize=8)

    # Опорные линии: 100% и 50%
    ax.axhline(1.0, ls="--", color="green", alpha=0.5, label="Идеальная (E=1)")
    ax.axhline(0.5, ls=":",  color="red",   alpha=0.5, label="Граница 50%")

    ax.set_xticks(x)
    ax.set_xticklabels(threads_list)
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Эффективность E(p) = S(p) / p")
    ax.set_title("Эффективность распараллеливания\n(красная обводка — наилучшая эффективность среди p > 1)")
    ax.set_ylim(0, 1.15)
    ax.grid(True, axis="y", ls=":", alpha=0.6)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "efficiency.png", dpi=140)
    plt.close(fig)

    # Таблица в stdout
    print()
    print(f"{'p':>4} | {'V1 time':>9} {'V1 S':>6} {'V1 E':>6} | "
          f"{'V2 time':>9} {'V2 S':>6} {'V2 E':>6}")
    print("-" * 66)
    by = {(r["version"], r["threads"]): r for v in versions for r in data[v]}
    for p in threads_list:
        r1, r2 = by.get(("v1", p)), by.get(("v2", p))
        t1, t2 = r1["time_s"], r2["time_s"]
        s1, s2 = T1/t1, T1/t2
        print(f"{p:>4} | {t1:>9.3f} {s1:>6.2f} {s1/p:>6.2f} | "
              f"{t2:>9.3f} {s2:>6.2f} {s2/p:>6.2f}")

    print("\nГрафики: results/time.png, speedup.png, efficiency.png")

if __name__ == "__main__":
    main()
