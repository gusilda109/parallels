#!/usr/bin/env python3
"""scripts/plot_schedule.py — столбчатая диаграмма параметров schedule().

Читает results/schedule.csv (формат: version,schedule,chunk,threads,N,iters,time_s)
и строит парные столбцы V1/V2 для каждого варианта schedule.
Подсвечивает лучший (минимальный по времени) вариант красной обводкой.

Сохраняет в results/schedule.png.
"""
from __future__ import annotations
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV  = ROOT / "results" / "schedule.csv"

rows = []
with CSV.open() as f:
    for r in csv.DictReader(f):
        rows.append({
            "version":  r["version"],            # v1 / v2
            "schedule": r["schedule"],           # static / dynamic / guided / auto
            "chunk":    int(r["chunk"]),
            "threads":  int(r["threads"]),
            "time_s":   float(r["time_s"]),
        })

# Собираем уникальные варианты schedule в стабильном порядке
order = []
seen = set()
for r in rows:
    key = (r["schedule"], r["chunk"])
    if key not in seen:
        seen.add(key)
        order.append(key)

# Удобные подписи для столбцов
def label(sch, ch):
    if ch == 0:
        return f"{sch}\n(default)"
    return f"{sch}\nchunk={ch}"

labels = [label(s, c) for s, c in order]

# Группируем по версии
by_v = {"v1": {}, "v2": {}}
for r in rows:
    by_v[r["version"]][(r["schedule"], r["chunk"])] = r["time_s"]

t_v1 = [by_v["v1"].get(k, 0) for k in order]
t_v2 = [by_v["v2"].get(k, 0) for k in order]

# Параметры замера (берём из первой строки CSV — они одинаковы для всех)
with CSV.open() as f:
    first = next(csv.DictReader(f))
threads = int(first["threads"])
N_val   = int(first["N"])

# ============ Рисуем ============
fig, ax = plt.subplots(figsize=(11, 6))
x = list(range(len(order)))
width = 0.38

bars_v1 = ax.bar([i - width/2 for i in x], t_v1, width,
                 color="tab:blue",   alpha=0.85, label="Variant V1")
bars_v2 = ax.bar([i + width/2 for i in x], t_v2, width,
                 color="tab:orange", alpha=0.85, label="Variant V2")

# Подписи значений над столбцами
for bars in (bars_v1, bars_v2):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + max(t_v1 + t_v2) * 0.01,
                f"{h:.3f}", ha="center", va="bottom", fontsize=9)

# Подсветка лучших (минимум по каждой версии)
def highlight_best(bars, times):
    if not times: return
    imin = times.index(min(times))
    bars[imin].set_edgecolor("red")
    bars[imin].set_linewidth(3)
    # Текст «best» под лучшим столбцом
    bars[imin].set_zorder(3)

highlight_best(bars_v1, t_v1)
highlight_best(bars_v2, t_v2)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=10)
ax.set_xlabel("Параметры schedule(...)")
ax.set_ylabel("Время работы, с")
ax.set_title(
    f"Сравнение параметров #pragma omp for schedule(...)\n"
    f"N = {N_val}, число потоков = {threads}, "
    f"красная обводка — наилучший результат")
ax.set_ylim(0, max(t_v1 + t_v2) * 1.15)
ax.grid(True, axis="y", ls=":", alpha=0.6)
ax.legend(loc="upper right")

fig.tight_layout()
out = ROOT / "results" / "schedule.png"
fig.savefig(out, dpi=140)
plt.close(fig)

# Таблица в stdout
print(f"Schedule analysis  (N={N_val}, threads={threads})")
print(f"{'schedule':>18} {'V1, с':>9} {'V2, с':>9}")
print("-" * 40)
for (sch, ch), tv1, tv2 in zip(order, t_v1, t_v2):
    tag = f"{sch}" + (f",{ch}" if ch else "")
    print(f"{tag:>18} {tv1:>9.3f} {tv2:>9.3f}")

print(f"\nВ1: лучший — {labels[t_v1.index(min(t_v1))].replace(chr(10), ' ')} "
      f"({min(t_v1):.3f} с)")
print(f"V2: лучший — {labels[t_v2.index(min(t_v2))].replace(chr(10), ' ')} "
      f"({min(t_v2):.3f} с)")
print(f"\nГрафик: {out}")
