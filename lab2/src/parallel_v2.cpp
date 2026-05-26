// parallel_v2.cpp — Вариант 2: одна #pragma omp parallel на весь алгоритм.
// Команда потоков создаётся один раз; синхронизация — через #pragma omp for
// (с неявным барьером) и #pragma omp single для скалярных операций.
//
// Сборка: g++ -O2 -std=c++17 -fopenmp -o parallel_v2 parallel_v2.cpp
// Запуск: OMP_NUM_THREADS=8 ./parallel_v2 <N> [schedule_kind] [chunk]

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

    // Параллельная инициализация для first-touch
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

    int    iter = 0;
    double rel_res = 0.0;
    double y_norm_sq_shared = 0.0;
    bool   done = false;
    int    nthreads = 0;

    auto t0 = std::chrono::high_resolution_clock::now();

    // ОДНА параллельная секция на весь алгоритм
    #pragma omp parallel
    {
        #pragma omp single
        nthreads = omp_get_num_threads();

        while (!done) {
            // Сброс общей суммы делает один поток
            #pragma omp single
            y_norm_sq_shared = 0.0;
            // неявный барьер после single — все увидят 0.0

            // y = A*x - b и редукция в y_norm_sq_shared.
            // Используем reduction на #pragma omp for — поддерживается стандартом
            // и не требует выхода из parallel-региона.
            double local_sum = 0.0;

            if (std::strcmp(sch, "dynamic") == 0) {
                if (chunk > 0) {
                    #pragma omp for schedule(dynamic, 1) nowait
                    for (int i = 0; i < N; ++i) {
                        double s = 0.0;
                        const double* Ai = &A[(size_t)i * N];
                        for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                        double yi = s - b[i];
                        y[i] = yi;
                        local_sum += yi * yi;
                    }
                } else {
                    #pragma omp for schedule(dynamic) nowait
                    for (int i = 0; i < N; ++i) {
                        double s = 0.0;
                        const double* Ai = &A[(size_t)i * N];
                        for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                        double yi = s - b[i];
                        y[i] = yi;
                        local_sum += yi * yi;
                    }
                }
            } else if (std::strcmp(sch, "guided") == 0) {
                #pragma omp for schedule(guided) nowait
                for (int i = 0; i < N; ++i) {
                    double s = 0.0;
                    const double* Ai = &A[(size_t)i * N];
                    for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                    double yi = s - b[i];
                    y[i] = yi;
                    local_sum += yi * yi;
                }
            } else if (std::strcmp(sch, "auto") == 0) {
                #pragma omp for schedule(auto) nowait
                for (int i = 0; i < N; ++i) {
                    double s = 0.0;
                    const double* Ai = &A[(size_t)i * N];
                    for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                    double yi = s - b[i];
                    y[i] = yi;
                    local_sum += yi * yi;
                }
            } else { // static
                if (chunk > 0) {
                    #pragma omp for schedule(static, 1) nowait
                    for (int i = 0; i < N; ++i) {
                        double s = 0.0;
                        const double* Ai = &A[(size_t)i * N];
                        for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                        double yi = s - b[i];
                        y[i] = yi;
                        local_sum += yi * yi;
                    }
                } else {
                    #pragma omp for schedule(static) nowait
                    for (int i = 0; i < N; ++i) {
                        double s = 0.0;
                        const double* Ai = &A[(size_t)i * N];
                        for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
                        double yi = s - b[i];
                        y[i] = yi;
                        local_sum += yi * yi;
                    }
                }
            }

            // Аккумулируем частичные суммы потоков
            #pragma omp atomic
            y_norm_sq_shared += local_sum;

            #pragma omp barrier  // дождаться всех редукций

            // Один поток проверяет критерий, при необходимости поднимает флаг
            #pragma omp single
            {
                rel_res = std::sqrt(y_norm_sq_shared) / b_norm;
                if (rel_res < eps || iter >= max_iter) done = true;
                ++iter;
            }
            // неявный барьер после single

            if (done) break;

            // x -= tau * y
            #pragma omp for schedule(static)
            for (int i = 0; i < N; ++i) x[i] -= tau * y[i];
            // неявный барьер — x синхронизирован к началу следующего шага
        }
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    double err = 0.0;
    for (int i = 0; i < N; ++i) {
        double d = std::fabs(x[i] - 1.0);
        if (d > err) err = d;
    }

    std::printf("V2 threads=%d schedule=%s chunk=%d N=%d iters=%d rel_res=%.3e err=%.3e time=%.3f\n",
                nthreads, sch, chunk, N, iter, rel_res, err, elapsed);
    return 0;
}
