cmake_minimum_required(VERSION 3.18)

# Включаем CUDA как полноценный язык сборки
project(sine_sum LANGUAGES CXX CUDA)

# ---- Опция выбора типа массива ----
# Использование:
#   cmake -B build -DUSE_DOUBLE=ON   -> double
#   cmake -B build -DUSE_DOUBLE=OFF  -> float  (по умолчанию)
option(USE_DOUBLE "Use double precision instead of float for array elements" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# Архитектуры GPU. Можно переопределить: -DCMAKE_CUDA_ARCHITECTURES=86
# 60 — Pascal (P100), 70 — Volta (V100), 75 — Turing (T4/2080),
# 80 — Ampere (A100), 86 — Ampere (3080/A40), 89 — Ada (4090), 90 — Hopper (H100)
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    set(CMAKE_CUDA_ARCHITECTURES 60 70 75 80 86 89 90)
endif()

add_executable(sine_sum src/main.cu)

# Прокидываем макрос USE_DOUBLE в код, если опция включена
if(USE_DOUBLE)
    target_compile_definitions(sine_sum PRIVATE USE_DOUBLE)
    message(STATUS ">>> Building with DOUBLE precision")
else()
    message(STATUS ">>> Building with FLOAT precision (default)")
endif()

# Оптимизации
target_compile_options(sine_sum PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:-O3 --use_fast_math=false>
    $<$<COMPILE_LANGUAGE:CXX>:-O3>
)
