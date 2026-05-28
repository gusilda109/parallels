# Лабораторная работа: многопоточность на C++

Две задачи. Сборка через CMake (или make), вычисления на сервере, график — Python.

## Структура

```
lab/
├── task1/              # умножение матрицы на вектор (std::thread)
│   ├── matvec.cpp
│   ├── run_benchmark.sh
│   └── CMakeLists.txt
├── task2/              # клиент-серверное приложение (шаблон класса)
│   ├── server.hpp      # сервер как шаблон класса TaskServer<Task, T>
│   ├── thread_pool.hpp # доп. задание: пул потоков (+3 балла)
│   ├── main.cpp        # 3 клиента: sin / sqrt / pow
│   ├── verify.cpp      # тест: читает файлы и проверяет результаты
│   └── CMakeLists.txt
└── plot/
    └── plot_speedup.py # график ускорения S_p(p) -> speedup.pdf
```

## Task 1 — анализ масштабируемости

Сборка и прогон на сервере:

```bash
cd task1
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
cp build/matvec .
chmod +x run_benchmark.sh
./run_benchmark.sh          # -> results.csv
./run_benchmark.sh pin      # с привязкой к ядрам -> results_pin.csv
```

Прогоняются потоки 1,2,4,7,8,16,20,40 для матриц 20000 и 40000.
Внимание: **40000×40000 double ≈ 12 ГиБ** — нужен сервер с достаточной ОЗУ.

Ускорение: `S_p = T_1 / T_p`. Эффективность: `E_p = S_p / p`.

График:

```bash
cd ../plot
python3 plot_speedup.py ../task1/results.csv
# или со сравнением привязки:
python3 plot_speedup.py ../task1/results.csv ../task1/results_pin.csv
```

## Task 2 — клиент-сервер

```bash
cd task2
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
cd build
./client_server     # генерирует results_sin.txt, results_sqrt.txt, results_pow.txt
./verify            # проверяет результаты, печатает ALL OK при успехе
# либо: ctest
```

Сервер — шаблон класса `TaskServer<Task, T>` с интерфейсом
`start() / stop() / add_task() / request_result()`.
Контейнер результатов — `std::unordered_map` (вставка/поиск по id в среднем O(1)).
Доступ к очереди и контейнеру синхронизирован (mutex + condition_variable).

## Требования к серверу для сборки
- компилятор с поддержкой C++20 (g++ 11+ / clang 13+)
- CMake 3.15+
- Python 3 + matplotlib (только для графика)
