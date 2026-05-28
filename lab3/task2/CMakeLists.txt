cmake_minimum_required(VERSION 3.15)
project(task2_client_server CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O2")

find_package(Threads REQUIRED)

add_executable(client_server main.cpp)
target_link_libraries(client_server PRIVATE Threads::Threads)

add_executable(verify verify.cpp)

enable_testing()
add_test(NAME run_app COMMAND client_server)
add_test(NAME verify_results COMMAND verify)
set_tests_properties(verify_results PROPERTIES DEPENDS run_app)
