# Makefile для лабораторной работы (Tasks.pdf — Задания 1, 2, 3)
CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra
OMPFLAGS ?= -fopenmp

SRC := src
BIN := bin

TARGETS := $(BIN)/serial $(BIN)/parallel_v1 $(BIN)/parallel_v2 \
           $(BIN)/task1_matvec $(BIN)/task2_integrate

.PHONY: all clean
all: $(TARGETS)

$(BIN):
	mkdir -p $(BIN)

# Задание 3 — последовательная и параллельные версии метода простой итерации
$(BIN)/serial: $(SRC)/serial.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/parallel_v1: $(SRC)/parallel_v1.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

$(BIN)/parallel_v2: $(SRC)/parallel_v2.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

# Задание 1 — параллельное умножение матрицы на вектор
$(BIN)/task1_matvec: $(SRC)/task1_matvec.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

# Задание 2 — параллельное численное интегрирование
$(BIN)/task2_integrate: $(SRC)/task2_integrate.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

clean:
	rm -rf $(BIN) results/*.csv
