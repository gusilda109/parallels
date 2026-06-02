#!/usr/bin/env python3
"""scripts/plot_profit.py — графики «эффективной производительности».

Метрика:  P_eff(p) = S(p) * E(p) = S(p)^2 / p
где S(p) — ускорение, E(p) — эффективность.

Эта комплексная метрика учитывает и скорость, и окупаемость ядер,
имеет чёткий максимум в точке оптимума (в отличие от S(p) и E(p)
по отдельности).

Строит три отдельных PNG в results/:
  - task1_profit.png  (Задание 1, по одной кривой на каждый N)
  - task2_profit.png  (Задание 2)
  - task3_profit.png  (Задание 3, V1 и V2)
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RES  = ROOT / "results"


def annotate_max(ax, xs, ys, color, label_prefix, y_offset=20):
    """Подсветить точку максимума."""
    imax = ys.index(max(ys))
    ax.scatter([xs[imax]], [ys[imax]], s=200, facecolor="none",
               edgecolor=color, linewidth=2.5, zorder=5)
    ax.annotate(f"{label_prefix}\nоптимум: p={xs[imax]}\nP_eff={ys[imax]:.2f}",
                xy=(xs[imax], ys[imax]), xytext=(15, y_offset),
                textcoords="offset points", fontsize=10, color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
                bbox=dict(boxstyle="round,pad=0.3", fc="white",
                          ec=color, alpha=0.85))


def style_axes(ax, title, threads=(1, 2, 4, 7, 8, 16, 20, 40)):
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Эффективная производительность  P_eff = S²/p")
    ax.set_title(title)
    ax.set_xticks(list(threads))
    ax.set_xticklabels([str(t) for t in threads])
    ax.grid(True, ls=":", alpha=0.6)
    ax.set_xlim(0.5, max(threads) + 2)
    # Запас сверху, чтобы аннотации не упирались в заголовок
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin, ymax * 1.18)


def print_table(label, xs, T1, times):
    """Печать таблицы метрики в stdout."""
    print(f"\n=== {label} ===  T(1) = {T1:.4f} с")
    print(f"{'p':>4} {'T(p), с':>10} {'S':>7} {'E':>7} {'P_eff':>8}")
    print("-" * 42)
    for p, t in zip(xs, times):
        s = T1 / t
        e = s / p
        peff = s * e
        print(f"{p:>4} {t:>10.4f} {s:>7.2f} {e:>7.2f} {peff:>8.3f}")


# ============ Задание 1 ============
def plot_task1():
    csv_path = RES / "task1.csv"
    if not csv_path.exists():
        print(f"[task1] {csv_path} нет — пропускаю")
        return

    by_N = defaultdict(list)
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            by_N[int(row["N"])].append((int(row["threads"]), float(row["time_s"])))

    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = ["tab:blue", "tab:orange", "tab:green"]
    all_threads = sorted({p for rows in by_N.values() for p, _ in rows})

    series = []
    for ci, N in enumerate(sorted(by_N.keys())):
        rows = sorted(by_N[N], key=lambda r: r[0])
        T1 = next(t for p, t in rows if p == 1)
        xs = [p for p, _ in rows]
        ts = [t for _, t in rows]
        ys = [(T1 / t) ** 2 / p for p, t in rows]

        color = colors[ci % len(colors)]
        ax.plot(xs, ys, marker="o", linewidth=2,
                label=f"N = {N}", color=color)
        series.append((N, xs, ys, color))
        print_table(f"Task1, N={N}", xs, T1, ts)

    series_sorted = sorted(series, key=lambda s: max(s[2]), reverse=True)
    for rank, (N, xs, ys, color) in enumerate(series_sorted):
        y_off = 25 if rank == 0 else -55
        annotate_max(ax, xs, ys, color, f"N={N}", y_offset=y_off)

    style_axes(ax,
               "Задание 1. Эффективная производительность P_eff = S²/p\n"
               "(круг — оптимальное число потоков)",
               threads=all_threads)
    ax.legend(loc="upper left")
    fig.tight_layout()
    out = RES / "task1_profit.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"  → {out}")


# ============ Задание 2 ============
def plot_task2():
    csv_path = RES / "task2.csv"
    if not csv_path.exists():
        print(f"[task2] {csv_path} нет — пропускаю")
        return

    rows = []
    with csv_path.open() as f:
        for r in csv.DictReader(f):
            rows.append((int(r["threads"]), float(r["time_s"])))
    rows.sort()
    T1 = next(t for p, t in rows if p == 1)

    xs = [p for p, _ in rows]
    ts = [t for _, t in rows]
    ys = [(T1 / t) ** 2 / p for p, t in rows]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    color = "tab:orange"
    ax.plot(xs, ys, marker="o", linewidth=2,
            color=color, label="integrate_omp")
    annotate_max(ax, xs, ys, color, "integrate_omp", y_offset=20)
    print_table("Task2", xs, T1, ts)

    style_axes(ax,
               "Задание 2. Эффективная производительность P_eff = S²/p\n"
               "(круг — оптимальное число потоков)",
               threads=xs)
    ax.legend(loc="upper left")
    fig.tight_layout()
    out = RES / "task2_profit.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"  → {out}")


# ============ Задание 3 ============
def plot_task3():
    csv_path = RES / "scaling.csv"
    if not csv_path.exists():
        print(f"[task3] {csv_path} нет — пропускаю")
        return

    rows = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            row["threads"] = int(row["threads"])
            row["time_s"]  = float(row["time_s"])
            rows.append(row)

    serial = next(r for r in rows if r["version"] == "serial")
    T1 = serial["time_s"]

    versions = ["v1", "v2"]
    colors = {"v1": "tab:blue", "v2": "tab:orange"}
    data = {v: sorted([r for r in rows if r["version"] == v],
                      key=lambda r: r["threads"]) for v in versions}

    fig, ax = plt.subplots(figsize=(9, 5.5))
    all_threads = sorted({r["threads"] for v in versions for r in data[v]})

    # Сначала строим линии
    series = []
    for v in versions:
        xs = [r["threads"] for r in data[v]]
        ts = [r["time_s"]  for r in data[v]]
        ys = [(T1 / t) ** 2 / p for p, t in zip(xs, ts)]
        ax.plot(xs, ys, marker="o", linewidth=2,
                label=f"Variant {v.upper()}", color=colors[v])
        series.append((v, xs, ts, ys))
        print_table(f"Task3, {v.upper()} (T_serial = {T1:.4f})", xs, T1, ts)

    # Сортируем серии по пику и аннотируем: верхнюю — выше, нижнюю — ниже
    series_sorted = sorted(series, key=lambda s: max(s[3]), reverse=True)
    for rank, (v, xs, ts, ys) in enumerate(series_sorted):
        # rank=0 — самая высокая, метку ставим выше пика
        # rank=1 — ниже, метку ставим ниже пика
        y_off = 25 if rank == 0 else -55
        annotate_max(ax, xs, ys, colors[v], v.upper(), y_offset=y_off)

    style_axes(ax,
               f"Задание 3. Эффективная производительность P_eff = S²/p\n"
               f"(T_serial = {T1:.2f} с; круг — оптимальное число потоков)",
               threads=all_threads)
    ax.legend(loc="upper left")
    fig.tight_layout()
    out = RES / "task3_profit.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"  → {out}")


if __name__ == "__main__":
    print("Считаю P_eff(p) = S(p)² / p для всех заданий…\n")
    plot_task1()
    plot_task2()
    plot_task3()
    print("\nГотово.")
