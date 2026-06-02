// task1_matvec.cpp — Задание 1: параллельное умножение матрицы на вектор.
//
// Семинар 1 Курносова: пишем многопоточную версию умножения y = A * x
// с ПАРАЛЛЕЛЬНОЙ ИНИЦИАЛИЗАЦИЕЙ массивов (для NUMA first-touch).
//
// Запуск: OMP_NUM_THREADS=p ./task1_matvec <N> [repeats]
//   N        — размер матрицы N x N (по умолчанию 20000)
//   repeats  — сколько раз повторить mat-vec (по умолчанию 5);
//              выводим минимум по повторам, чтобы шум измерения был меньше.
//
// Замечания по корректности замера:
//   * Mat-vec — операция короткая. Чтобы получить устойчивые цифры,
//     запускаем её несколько раз и берём минимум.
//   * Инициализация делается ПАРАЛЛЕЛЬНО — это критично для NUMA:
//     благодаря first-touch страницы массивов попадают в локальную
//     память тех потоков, которые их потом будут читать.

#include <cstdio>
#include <cstdlib>
#include <vector>
#include <chrono>
#include <omp.h>

int main(int argc, char** argv) {
    int N       = (argc > 1) ? std::atoi(argv[1]) : 20000;
    int repeats = (argc > 2) ? std::atoi(argv[2]) : 5;

    // Память. (size_t)N*N важно для N >= ~46341 (где N*N переполняет int).
    std::vector<double> A(static_cast<size_t>(N) * N);
    std::vector<double> x(N), y(N);

    int nthreads = 0;

    // ----- Параллельная инициализация (first-touch) -----
    #pragma omp parallel
    {
        #pragma omp single
        nthreads = omp_get_num_threads();

        // x и y трогаем тем же распределением, что и A (по строкам i),
        // чтобы они оказались на тех же NUMA-нодах.
        #pragma omp for schedule(static)
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                // Произвольные значения, зависящие только от (i, j),
                // — задача одна и та же на любом числе потоков.
                A[(size_t)i * N + j] = (i == j) ? 2.0 : 1.0;
            }
            x[i] = 1.0;
            y[i] = 0.0;
        }
    }

    // ----- Замер: репитим mat-vec, берём минимум -----
    double best = 1e300;
    for (int r = 0; r < repeats; ++r) {
        auto t0 = std::chrono::high_resolution_clock::now();

        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i) {
            double s = 0.0;
            const double* Ai = &A[(size_t)i * N];
            for (int j = 0; j < N; ++j) s += Ai[j] * x[j];
            y[i] = s;
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        double t = std::chrono::duration<double>(t1 - t0).count();
        if (t < best) best = t;
    }

    // Контрольное значение (защита от того, чтобы компилятор не выкинул
    // вычисление как «неиспользованное»). Для нашей матрицы и x=1
    // y[i] должен равняться N + 1.
    double check = y[0];

    std::printf("threads=%d N=%d repeats=%d best_time=%.4f s y[0]=%.1f\n",
                nthreads, N, repeats, best, check);
    return 0;
}
