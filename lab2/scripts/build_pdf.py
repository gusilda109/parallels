#!/usr/bin/env python3
"""scripts/build_pdf.py — собирает все PNG из results/ в один PDF."""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.image import imread

ROOT = Path(__file__).resolve().parents[1]
RES  = ROOT / "results"
OUT  = ROOT / "results" / (sys.argv[1] if len(sys.argv) > 1 else "report.pdf")

PAGES = [
    ("task1_speedup.png",  "Задание 1. Ускорение умножения матрицы на вектор"),
    ("task1_profit.png",   "Задание 1. Эффективная производительность P_eff = S²/p"),
    ("task2_speedup.png",  "Задание 2. Ускорение численного интегрирования"),
    ("task2_profit.png",   "Задание 2. Эффективная производительность P_eff = S²/p"),
    ("time.png",           "Задание 3. Время работы (метод простой итерации)"),
    ("speedup.png",        "Задание 3. Ускорение"),
    ("efficiency.png",     "Задание 3. Эффективность"),
    ("task3_profit.png",   "Задание 3. Эффективная производительность P_eff = S²/p"),
]

found = [(RES / fn, title) for fn, title in PAGES if (RES / fn).exists()]
missing = [fn for fn, _ in PAGES if not (RES / fn).exists()]
if missing:
    print(f"Пропущены (не найдены в results/): {', '.join(missing)}")

if not found:
    print("Не найдено ни одного PNG. Сначала запустите plot-скрипты.")
    sys.exit(1)

with PdfPages(OUT) as pdf:
    for path, title in found:
        img = imread(path)
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(title, fontsize=14, pad=20)
        fig.tight_layout()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
        print(f"  +  {path.name}  ({title})")

print(f"\nГотово: {OUT}")
