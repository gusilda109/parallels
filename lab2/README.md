# Параллельное программирование — Задания 1, 2, 3

Три задания из `Tasks.pdf`:
- **Задание 1**: параллельное умножение матрицы на вектор (OpenMP), N = 20000 и 40000.
- **Задание 2**: параллельное численное интегрирование с `#pragma omp atomic`, nsteps = 40 000 000.
- **Задание 3**: Лабораторная работа №2 — метод простой итерации для СЛАУ Ax = b в двух OpenMP-вариантах.

## Структура

```
lab2/
├── Makefile
├── src/
│   ├── task1_matvec.cpp          ← Задание 1
│   ├── task2_integrate.cpp       ← Задание 2
│   ├── serial.cpp                ← Задание 3 (baseline)
│   ├── parallel_v1.cpp           ← Задание 3 (вариант 1)
│   └── parallel_v2.cpp           ← Задание 3 (вариант 2)
├── scripts/
│   ├── run_task1.sh / plot_task1.py
│   ├── run_task2.sh / plot_task2.py
│   ├── run_scaling.sh / plot.py  ← Задание 3
│   └── run_schedule.sh           ← Задание 3, пункт 3
└── results/                      ← CSV + PNG (создаются при запуске)
```

## Сборка

```bash
make           # соберёт все 5 бинарников
ls bin/
```

## Запуск замеров на сервере

### Задание 1 — умножение матрицы на вектор

```bash
./scripts/run_task1.sh 5         # 5 повторов
# время: ~5-15 минут (N=40000 на малом числе потоков долго)
python3 scripts/plot_task1.py
# результат: results/task1.csv, results/task1_speedup.png
```

### Задание 2 — численное интегрирование

```bash
./scripts/run_task2.sh 40000000 5
python3 scripts/plot_task2.py
# результат: results/task2.csv, results/task2_speedup.png
```

### Задание 3 — метод простой итерации

```bash
./bin/serial 25000              # подобрать N (требование T(1) >= 30 с)
./scripts/run_scaling.sh 25000 3
./scripts/run_schedule.sh 25000 16 3
python3 scripts/plot.py
```

## Запускайте через tmux

Замеры идут долго (десятки минут). Чтобы не оборвалась ssh-сессия:

```bash
tmux new -s lab
./scripts/run_task1.sh 5
# Ctrl+B, потом D — отсоединиться
tmux attach -t lab                # вернуться
```
