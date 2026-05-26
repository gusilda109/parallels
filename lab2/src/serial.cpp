// serial.cpp — последовательная реализация метода простой итерации
// Решает Ax = b, где a_ii = 2.0, a_ij = 1.0 (i != j), b_i = N + 1.
// Точное решение: x_i = 1.0.
//
// Сборка: g++ -O2 -std=c++17 -o serial serial.cpp
// Запуск: ./serial <N>

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <chrono>

int main(int argc, char** argv) {
    int N = (argc > 1) ? std::atoi(argv[1]) : 15000;
    const double tau = 0.0001;       // параметр метода; знак подобран
    const double eps = 1e-5;
    const int    max_iter = 100000;

    // Выделение памяти
    std::vector<double> A(static_cast<size_t>(N) * N);
    std::vector<double> b(N), x(N, 0.0), Ax(N);

    // Инициализация (как в задаче с заданным решением)
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) A[(size_t)i * N + j] = (i == j) ? 2.0 : 1.0;
        b[i] = N + 1.0;
    }

    // ||b||_2
    double b_norm_sq = 0.0;
    for (int i = 0; i < N; ++i) b_norm_sq += b[i] * b[i];
    const double b_norm = std::sqrt(b_norm_sq);

    auto t0 = std::chrono::high_resolution_clock::now();

    int iter = 0;
    double rel_res = 0.0;
    for (; iter < max_iter; ++iter) {
        // y = A*x - b ; одновременно считаем ||y||^2
        double y_norm_sq = 0.0;
        for (int i = 0; i < N; ++i) {
            double s = 0.0;
            for (int j = 0; j < N; ++j) s += A[(size_t)i * N + j] * x[j];
            double yi = s - b[i];
            Ax[i] = yi;             // сохраняем y_i
            y_norm_sq += yi * yi;
        }

        rel_res = std::sqrt(y_norm_sq) / b_norm;
        if (rel_res < eps) break;

        // x = x - tau * y
        for (int i = 0; i < N; ++i) x[i] -= tau * Ax[i];
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    // Проверка качества: ||x - 1||_inf
    double err = 0.0;
    for (int i = 0; i < N; ++i) err = std::max(err, std::fabs(x[i] - 1.0));

    std::printf("N=%d  iters=%d  rel_res=%.3e  ||x-1||_inf=%.3e  time=%.3f s\n",
                N, iter, rel_res, err, elapsed);
    return 0;
}
