#!/usr/bin/env python3
import sys, csv
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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
                label=f"M = N = {n}", linewidth=2, markersize=6)

    ideal = list(range(1, max_p + 1))
    ax.plot(ideal, ideal, "--", color="gray", linewidth=1.5, label="Линейное")

    ax.set_xlabel("Число потоков р", fontsize=13)
    ax.set_ylabel("Ускорение S(p)", fontsize=13)
    ax.set_title("Ускорение распараллеливания", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.4, linestyle="--")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    fig.tight_layout()
    fig.savefig("speedup.pdf")
    fig.savefig("speedup.png", dpi=150)
    print("Saved speedup.pdf and speedup.png")

if __name__ == "__main__":
    main()
