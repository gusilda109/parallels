#!/usr/bin/env python3
"""scripts/plot.py — графики времени, ускорения и эффективности.

Читает results/scaling.csv (формат: version,threads,N,iters,time_s,rel_res,err)
и сохраняет PNG-файлы:
  - results/time.png
  - results/speedup.png
  - results/efficiency.png
Также печатает итоговую сводную таблицу.
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

def main():
    rows = load()
    serial = next(r for r in rows if r["version"] == "serial")
    T1 = serial["time_s"]
    print(f"Serial T(1) = {T1:.3f} s, N = {serial['N']}")

    versions = ["v1", "v2"]
    data = {v: sorted([r for r in rows if r["version"] == v], key=lambda r: r["threads"]) for v in versions}

    # --- График времени ---
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhline(T1, ls="--", color="gray", label=f"Serial T(1)={T1:.1f}s")
    for v in versions:
        xs = [r["threads"]    for r in data[v]]
        ys = [r["time_s"]     for r in data[v]]
        ax.plot(xs, ys, marker="o", label=f"Variant {v.upper()}")
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Время, с")
    ax.set_title("Время работы от числа потоков")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.grid(True, which="both", ls=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "time.png", dpi=140)
    plt.close(fig)

    # --- Ускорение S(p) = T1 / Tp ---
    fig, ax = plt.subplots(figsize=(7, 5))
    max_p = max(r["threads"] for v in versions for r in data[v])
    ax.plot([1, max_p], [1, max_p], ls="--", color="gray", label="Линейное")
    for v in versions:
        xs = [r["threads"] for r in data[v]]
        ys = [T1 / r["time_s"] for r in data[v]]
        ax.plot(xs, ys, marker="o", label=f"Variant {v.upper()}")
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Ускорение S(p)")
    ax.set_title("Ускорение распараллеливания")
    ax.grid(True, ls=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "speedup.png", dpi=140)
    plt.close(fig)

    # --- Эффективность E(p) = S(p) / p ---
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhline(1.0, ls="--", color="gray", label="Идеальная")
    for v in versions:
        xs = [r["threads"] for r in data[v]]
        ys = [(T1 / r["time_s"]) / r["threads"] for r in data[v]]
        ax.plot(xs, ys, marker="o", label=f"Variant {v.upper()}")
    ax.set_xlabel("Число потоков p")
    ax.set_ylabel("Эффективность E(p)")
    ax.set_title("Эффективность распараллеливания")
    ax.set_ylim(0, 1.1)
    ax.grid(True, ls=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "efficiency.png", dpi=140)
    plt.close(fig)

    # --- Таблица ---
    print()
    print(f"{'p':>4} | {'V1 time':>9} {'V1 S':>6} {'V1 E':>6} | {'V2 time':>9} {'V2 S':>6} {'V2 E':>6}")
    print("-" * 64)
    ps = sorted({r["threads"] for v in versions for r in data[v]})
    by = {(r["version"], r["threads"]): r for v in versions for r in data[v]}
    for p in ps:
        r1 = by.get(("v1", p)); r2 = by.get(("v2", p))
        t1 = r1["time_s"] if r1 else float("nan")
        t2 = r2["time_s"] if r2 else float("nan")
        s1 = T1 / t1 if r1 else float("nan")
        s2 = T1 / t2 if r2 else float("nan")
        print(f"{p:>4} | {t1:>9.3f} {s1:>6.2f} {s1/p:>6.2f} | {t2:>9.3f} {s2:>6.2f} {s2/p:>6.2f}")

    print(f"\nГрафики: results/time.png, speedup.png, efficiency.png")

if __name__ == "__main__":
    main()
