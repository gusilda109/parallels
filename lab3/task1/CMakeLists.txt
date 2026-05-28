cmake_minimum_required(VERSION 3.15)
project(task1_matvec CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native")

add_executable(matvec matvec.cpp)

find_package(Threads REQUIRED)
target_link_libraries(matvec PRIVATE Threads::Threads)
