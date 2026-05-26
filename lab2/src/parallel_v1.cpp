// parallel_v1.cpp — Вариант 1: на каждый распараллеливаемый цикл своя секция
// #pragma omp parallel for. Накладные расходы на создание/завершение
// команды потоков платятся на каждой итерации внешнего цикла.
//
// Сборка: g++ -O2 -std=c++17 -fopenmp -o parallel_v1 parallel_v1.cpp
// Запуск: OMP_NUM_THREADS=8 ./parallel_v1 <N> [schedule_kind] [chunk]
//   schedule_kind: static|dynamic|guided|auto  (по умолчанию static)
//   chunk:         целое (по умолчанию 0 => без указания chunk)

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <vector>
#include <chrono>
#include <omp.h>

int main(int argc, char** argv) {
    int N = (argc > 1) ? std::atoi(argv[1]) : 15000;
    const char* sch = (argc > 2) ? argv[2] : "static";
    int chunk = (argc > 3) ? std::atoi(argv[3]) : 0;

    const double tau = 1e-5;
    const double eps = 1e-5;
    const int    max_iter = 100000;

    std::vector<double> A(static_cast<size_t>(N) * N);
    std::vector<double> b(N), x(N, 0.0), y(N);

    // Параллельная инициализация (важно для NUMA: страницы попадают
    // в локальную для потока память — first-touch policy).
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) A[(size_t)i * N + j] = (i == j) ? 2.0 : 1.0;
        b[i] = N + 1.0;
        x[i] = 0.0;
        y[i] = 0.0;
    }

    double b_norm_sq = 0.0;
    #pragma omp parallel for reduction(+:b_norm_sq) schedule(static)
    for (int i = 0; i < N; ++i) b_norm_sq += b[i] * b[i];
    const double b_norm = std::sqrt(b_norm_sq);

    int nthreads = 0;
    #pragma omp parallel
    {
        #pragma omp single
        nthreads = omp_get_num_threads();
    }

    auto t0 = std::chrono::high_resolution_clock::now();

    int iter = 0;
    double rel_res = 0.0;
    for (; iter < max_iter; ++iter) {
        double y_norm_sq = 0.0;

        // y = A*x - b и одновременно ||y||^2
        if (std::strcmp(sch, "dynamic") == 0) {
            if (chunk > 0) {
                #pragma omp parallel for reduction(+:y_norm_sq) schedule(dynamic, chunk == 0 ? 1 : chunk)
                for (int i = 0; i < N; ++i) {
                    double s = 0.0;
                    const double* Ai = &A[(size_t)i * N];
                    for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                    double yi = s - b[i];
                    y[i] = yi;
                    y_norm_sq += yi * yi;
                }
            } else {
                #pragma omp parallel for reduction(+:y_norm_sq) schedule(dynamic)
                for (int i = 0; i < N; ++i) {
                    double s = 0.0;
                    const double* Ai = &A[(size_t)i * N];
                    for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                    double yi = s - b[i];
                    y[i] = yi;
                    y_norm_sq += yi * yi;
                }
            }
        } else if (std::strcmp(sch, "guided") == 0) {
            #pragma omp parallel for reduction(+:y_norm_sq) schedule(guided)
            for (int i = 0; i < N; ++i) {
                double s = 0.0;
                const double* Ai = &A[(size_t)i * N];
                for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                double yi = s - b[i];
                y[i] = yi;
                y_norm_sq += yi * yi;
            }
        } else if (std::strcmp(sch, "auto") == 0) {
            #pragma omp parallel for reduction(+:y_norm_sq) schedule(auto)
            for (int i = 0; i < N; ++i) {
                double s = 0.0;
                const double* Ai = &A[(size_t)i * N];
                for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                double yi = s - b[i];
                y[i] = yi;
                y_norm_sq += yi * yi;
            }
        } else { // static
            if (chunk > 0) {
                #pragma omp parallel for reduction(+:y_norm_sq) schedule(static, 1)
                for (int i = 0; i < N; ++i) {
                    double s = 0.0;
                    const double* Ai = &A[(size_t)i * N];
                    for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                    double yi = s - b[i];
                    y[i] = yi;
                    y_norm_sq += yi * yi;
                }
            } else {
                #pragma omp parallel for reduction(+:y_norm_sq) schedule(static)
                for (int i = 0; i < N; ++i) {
                    double s = 0.0;
                    const double* Ai = &A[(size_t)i * N];
                    for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                    double yi = s - b[i];
                    y[i] = yi;
                    y_norm_sq += yi * yi;
                }
            }
        }

        rel_res = std::sqrt(y_norm_sq) / b_norm;
        if (rel_res < eps) break;

        // x -= tau * y — отдельная параллельная секция
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i) x[i] -= tau * y[i];
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    double err = 0.0;
    for (int i = 0; i < N; ++i) {
        double d = std::fabs(x[i] - 1.0);
        if (d > err) err = d;
    }

    std::printf("V1 threads=%d schedule=%s chunk=%d N=%d iters=%d rel_res=%.3e err=%.3e time=%.3f\n",
                nthreads, sch, chunk, N, iter, rel_res, err, elapsed);
    return 0;
}
