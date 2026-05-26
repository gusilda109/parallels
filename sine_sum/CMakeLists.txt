cmake_minimum_required(VERSION 3.10)
project(sine_sum LANGUAGES CXX)

option(USE_DOUBLE "Use double precision instead of float" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(sine_sum src/main.cpp)

if(USE_DOUBLE)
    target_compile_definitions(sine_sum PRIVATE USE_DOUBLE)
    message(STATUS ">>> Building with DOUBLE precision")
else()
    message(STATUS ">>> Building with FLOAT precision (default)")
endif()

target_compile_options(sine_sum PRIVATE -O3)