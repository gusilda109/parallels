# Makefile для лабораторной работы №2 (OpenMP)
CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra
OMPFLAGS ?= -fopenmp

SRC := src
BIN := bin

TARGETS := $(BIN)/serial $(BIN)/parallel_v1 $(BIN)/parallel_v2

.PHONY: all clean
all: $(TARGETS)

$(BIN):
	mkdir -p $(BIN)

$(BIN)/serial: $(SRC)/serial.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/parallel_v1: $(SRC)/parallel_v1.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

$(BIN)/parallel_v2: $(SRC)/parallel_v2.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

clean:
	rm -rf $(BIN) results/*.csv
