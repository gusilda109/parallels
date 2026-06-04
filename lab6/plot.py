#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GRIDS = [128, 256, 512, 1024]
LABELS = [f"{g}x{g}" for g in GRIDS]


def load_results(path="results.csv"):
    data = {}
    if not os.path.exists(path):
        print(f"нет {path} — пропускаю графики по сеткам")
        return data
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                data.setdefault(row["target"], {})[int(row["grid"])] = float(row["time"])
            except (ValueError, KeyError):
                pass
    return data


def series(data, target):
    d = data.get(target, {})
    return [d.get(g, 0.0) for g in GRIDS]


def chart_cpu_one_vs_multi(data):
    one, multi = series(data, "cpu_onecore"), series(data, "cpu_multicore")
    x = range(len(GRIDS)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - w/2 for i in x], one,   w, label="CPU onecore")
    ax.bar([i + w/2 for i in x], multi, w, label="CPU multicore")
    ax.set_xticks(list(x)); ax.set_xticklabels(LABELS)
    ax.set_ylabel("Время, с"); ax.set_title("CPU onecore vs multicore")
    ax.legend(); fig.tight_layout(); fig.savefig("chart_cpu_one_vs_multi.png", dpi=140)
    print("chart_cpu_one_vs_multi.png")


def chart_all(data):
    x = range(len(GRIDS)); w = 0.27
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([i - w for i in x], series(data, "cpu_onecore"),   w, label="CPU onecore")
    ax.bar([i     for i in x], series(data, "cpu_multicore"), w, label="CPU multicore")
    ax.bar([i + w for i in x], series(data, "gpu"),           w, label="GPU")
    ax.set_xticks(list(x)); ax.set_xticklabels(LABELS)
    ax.set_ylabel("Время, с"); ax.set_title("CPU-one / CPU-multi / GPU")
    ax.legend(); fig.tight_layout(); fig.savefig("chart_all.png", dpi=140)
    print("chart_all.png")


def chart_stages(path="stages.csv"):
    if not os.path.exists(path):
        print(f"нет {path} — пропускаю график этапов (создай stage,time)")
        return
    stages, times = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            stages.append(row["stage"]); times.append(float(row["time"]))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stages, times, marker="o")
    ax.set_xlabel("Этап оптимизации"); ax.set_ylabel("Время, с")
    ax.set_title("Оптимизация GPU (сетка 512x512)")
    for s, t in zip(stages, times):
        ax.annotate(f"{t:.3f}", (s, t), textcoords="offset points", xytext=(0, 8), ha="center")
    fig.tight_layout(); fig.savefig("chart_stages.png", dpi=140)
    print("chart_stages.png")


if __name__ == "__main__":
    data = load_results()
    if data:
        chart_cpu_one_vs_multi(data)
        chart_all(data)
    chart_stages()
    print("готово")