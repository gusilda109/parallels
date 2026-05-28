#!/usr/bin/env python3
"""Сборка короткого PDF-отчёта по Task 1: график + таблицы."""

import sys
import csv
import os
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if os.path.exists(_reg):
    pdfmetrics.registerFont(TTFont("DejaVu", _reg))
    FONT_NAME = "DejaVu"
    if os.path.exists(_bold):
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", _bold))
        FONT_BOLD = "DejaVu-Bold"
    else:
        FONT_BOLD = "DejaVu"


def read_results(path):
    data = defaultdict(dict)
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            n, p, t = int(row[0]), int(row[1]), float(row[2])
            data[n][p] = t
    return data


def build_table(times):
    t1 = times.get(1) or times[min(times)] * min(times)
    rows = [["p", "T_p, с", "S_p = T_1/T_p", "E_p = S_p/p"]]
    for p in sorted(times):
        tp = times[p]
        sp = t1 / tp
        rows.append([str(p), f"{tp:.6f}", f"{sp:.2f}", f"{sp/p:.2f}"])
    return rows


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "results.csv"
    img_path = sys.argv[2] if len(sys.argv) > 2 else "speedup.png"
    data = read_results(csv_path)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=15, fontName=FONT_BOLD)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, fontName=FONT_BOLD)
    normal = ParagraphStyle("body", parent=styles["Normal"], fontName=FONT_NAME)

    doc = SimpleDocTemplate("report.pdf", pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    story.append(Paragraph("Лабораторная работа 3. Анализ эффективности", h1))
    story.append(Paragraph(
        "Задание 1. Многопоточное умножение матрицы на вектор (std::thread), "
        "double, параллельная инициализация массивов. Сервер: 80 ядер, 754 ГиБ ОЗУ.",
        normal))
    story.append(Spacer(1, 8))
    story.append(Paragraph("График ускорения S_p(p)", h2))
    img = Image(img_path)
    max_w = 16 * cm
    img.drawHeight = max_w * img.imageHeight / img.imageWidth
    img.drawWidth = max_w
    story.append(img)
    story.append(Spacer(1, 10))

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ])
    for n in sorted(data):
        gib = "~3 ГиБ" if n == 20000 else "~12 ГиБ"
        story.append(Paragraph(f"M = N = {n} ({gib})", h2))
        tbl = Table(build_table(data[n]), colWidths=[2*cm, 4*cm, 4.5*cm, 4*cm])
        tbl.setStyle(table_style)
        story.append(tbl)
        story.append(Spacer(1, 10))

    story.append(Paragraph("Вывод о масштабируемости", h2))
    story.append(Paragraph(
        "Умножение матрицы на вектор ограничено пропускной способностью памяти "
        "(memory-bound): на каждый элемент приходится одно умножение и сложение, "
        "а матрица целиком читается из памяти. До 7-8 потоков ускорение растёт "
        "почти линейно (S_p близко к p, эффективность около 1), затем выходит на "
        "плато порядка 8x: потоки упираются в пропускную способность памяти. "
        "Бо́льшая матрица (40000) использует ресурсы чуть лучше. Колебания в "
        "средней части объясняются конкуренцией за кэш и NUMA-эффектами.",
        normal))
    doc.build(story)
    print("Saved report.pdf")


if __name__ == "__main__":
    main()
