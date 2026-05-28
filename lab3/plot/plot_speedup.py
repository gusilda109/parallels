#!/usr/bin/env python3
"""Построение графика ускорения S_p(p) для Task 1.

Читает results.csv (формат: N,threads,time_seconds), считает ускорение
S_p = T_1 / T_p для каждого размера матрицы и строит график вместе с
линией идеального (линейного) ускорения.

Usage:
    python3 plot_speedup.py results.csv [results_pin.csv]
Выход: speedup.pdf и speedup.png
"""

import sys
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_results(path):
    """Возвращает dict: {N: {threads: time}}."""
    data = defaultdict(dict)
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            n = int(row[0])
            p = int(row[1])
            t = float(row[2])
            data[n][p] = t
    return data


def speedup(times):
    """times: {threads: time} -> (xs, ys) c S_p = T_1/T_p."""
    if 1 not in times:
        base_p = min(times)
        t1 = times[base_p] * base_p  # грубая оценка, если нет T_1
    else:
        t1 = times[1]
    xs = sorted(times)
    ys = [t1 / times[p] for p in xs]
    return xs, ys


def main():
    if len(sys.argv) < 2:
        print("Usage: plot_speedup.py results.csv [results_pin.csv]")
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(8, 6))

    colors = {20000: "tab:red", 40000: "tab:orange"}
    max_p = 1

    for arg_i, path in enumerate(sys.argv[1:]):
        data = read_results(path)
        suffix = "" if arg_i == 0 else " (pinned)"
        style = "-o" if arg_i == 0 else "--s"
        for n, times in sorted(data.items()):
            xs, ys = speedup(times)
            max_p = max(max_p, max(xs))
            ax.plot(xs, ys, style, color=colors.get(n, None),
                    label=f"M = N = {n}{suffix}")

    # Линия идеального ускорения.
    ideal = list(range(1, max_p + 1))
    ax.plot(ideal, ideal, "b--", alpha=0.6, label="Linear (ideal)")

    ax.set_xlabel("p (число потоков)")
    ax.set_ylabel("$S_p$ (ускорение)")
    ax.set_title("Ускорение умножения матрицы на вектор")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig("speedup.pdf")
    fig.savefig("speedup.png", dpi=150)
    print("Saved speedup.pdf and speedup.png")


if __name__ == "__main__":
    main()
