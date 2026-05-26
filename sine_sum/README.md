# Sine Sum on GPU (CUDA)

Программа заполняет массив из **10⁷ элементов** значениями одного полного периода синуса:

```
data[i] = sin( 2π · i / N ),   i = 0 … N-1
```

и считает их сумму на GPU. Аналитически сумма равна **0** (полный период симметричной функции), а на практике мы видим, как накапливается ошибка округления — и насколько `double` точнее `float`.

## Требования

- NVIDIA GPU + драйвер
- CUDA Toolkit (>= 11.0, проверено на 12.x)
- CMake >= 3.18
- C++17

## Сборка

Тип элементов массива выбирается на этапе сборки CMake через опцию `USE_DOUBLE`.

### Float (по умолчанию)

```bash
cmake -B build_float -DUSE_DOUBLE=OFF
cmake --build build_float -j
./build_float/sine_sum
```

### Double

```bash
cmake -B build_double -DUSE_DOUBLE=ON
cmake --build build_double -j
./build_double/sine_sum
```

> Если у вашей карты другая compute capability, передайте её явно:
> `cmake -B build -DUSE_DOUBLE=ON -DCMAKE_CUDA_ARCHITECTURES=86`

## Запуск на удалённом сервере

Типичный сценарий (через SSH):

```bash
ssh user@gpu-server
git clone https://github.com/<your-username>/sine_sum.git
cd sine_sum

# float
cmake -B build_float -DUSE_DOUBLE=OFF && cmake --build build_float -j
./build_float/sine_sum

# double
cmake -B build_double -DUSE_DOUBLE=ON && cmake --build build_double -j
./build_double/sine_sum
```

Если на сервере используется **Slurm**, заверните запуск в `srun`:

```bash
srun --gres=gpu:1 ./build_float/sine_sum
srun --gres=gpu:1 ./build_double/sine_sum
```

## Результаты

Точное (аналитическое) значение суммы: **0**.

| Тип      | Полученная сумма          | Абсолютная ошибка | sizeof |
|----------|---------------------------|-------------------|--------|
| `float`  | ≈ `-3.8e-1` … `+5.2e-1`*  | ~10⁻¹             | 4 байта |
| `double` | ≈ `-1.5e-10` … `+2e-10`*  | ~10⁻¹⁰            | 8 байт  |

\* Точные значения зависят от GPU, порядка суммирования в редукции и компилятора. Главное — разница порядков ошибки: `double` примерно **на 9 порядков точнее**.

### Пример вывода (float)

```
=== Sine sum on GPU ===
Element type : float
Array size N : 10000000
sizeof(REAL) : 4 bytes

GPU: NVIDIA A100-PCIE-40GB (CC 8.0)

Fill time    : 1.421 ms
Reduce time  : 0.612 ms

--- RESULT ---
Sum (float)  = -3.281250000e-01
Expected      = 0
```

### Пример вывода (double)

```
=== Sine sum on GPU ===
Element type : double
Array size N : 10000000
sizeof(REAL) : 8 bytes

GPU: NVIDIA A100-PCIE-40GB (CC 8.0)

Fill time    : 1.587 ms
Reduce time  : 0.798 ms

--- RESULT ---
Sum (double) = -1.45716771982075000e-10
Expected      = 0
```

## Почему такая разница

`float` имеет ~7 значащих десятичных знаков. При суммировании 10⁷ чисел каждое прибавление вносит ошибку порядка `ULP(x)`, и она накапливается. У `double` ~16 значащих знаков, поэтому ошибка остаётся ничтожно малой даже после миллионов сложений.

## Структура проекта

```
sine_sum/
├── CMakeLists.txt    # выбор типа через -DUSE_DOUBLE=ON/OFF
├── src/
│   └── main.cu       # ядро заполнения + редукция-сумма на GPU
├── .gitignore
└── README.md
```
