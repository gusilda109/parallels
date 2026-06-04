#!/usr/bin/env python3
import sys, csv
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def read_results(path):
    data = defaultdict(dict)
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 3: continue
            n, p, t = int(row[0]), int(row[1]), float(row[2])
            data[n][p] = t
    return data

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "results.csv"
    data = read_results(csv_path)
    sizes = sorted(data.keys())
    fig, ax = plt.subplots(figsize=(10, 7))
    colors_list = ["tab:blue", "tab:orange"]
    max_p = 1
    for i, n in enumerate(sizes):
        t1 = data[n][1]
        xs = sorted(data[n])
        ys = [t1 / data[n][p] for p in xs]
        max_p = max(max_p, max(xs))
        ax.plot(xs, ys, "-o", color=colors_list[i],
                label=f"N = {n}", linewidth=2, markersize=5)
        max_s = max(ys)
        max_p_val = xs[ys.index(max_s)]
        ax.plot(max_p_val, max_s, "o", color=colors_list[i],
                markersize=14, fillstyle="none", linewidth=2)
        ax.annotate(f"N={n}\nmax: p={max_p_val}, S={max_s:.1f}x",
                    xy=(max_p_val, max_s),
                    xytext=(max_p_val + 1, max_s + 0.3),
                    color=colors_list[i], fontsize=9)
    ideal = list(range(1, max_p + 1))
    ax.plot(ideal, ideal, "--", color="gray", linewidth=1.5, label="Идеальное (линейное)")
    ax.set_xlabel("Число потоков р", fontsize=13)
    ax.set_ylabel("Ускорение S(p) = T(1)/T(p)", fontsize=13)
    ax.set_title("Задание 1. Ускорение умножения матрицы на вектор\n(круг — точка максимального ускорения)", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.4, linestyle="--")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig("speedup.pdf")
    fig.savefig("speedup.png", dpi=150)
    print("Saved speedup.pdf and speedup.png")

if __name__ == "__main__":
    main()
