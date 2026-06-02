// task2_integrate.cpp — Задание 2: параллельное численное интегрирование
// методом прямоугольников/трапеций.
//
// Семинар 2 Курносова: функция integrate_omp использует локальную
// переменную и #pragma omp atomic для аккумуляции частичных сумм.
//
// Берём классический «учебный» интеграл  ∫_0^1 4/(1+x^2) dx = π.
// Это удобно: можно сравнить результат с известным значением.
//
// Запуск: OMP_NUM_THREADS=p ./task2_integrate [nsteps] [repeats]
//   nsteps  — число точек интегрирования (по умолчанию 40 000 000)
//   repeats — сколько раз повторить (по умолчанию 5)

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <chrono>
#include <omp.h>

static inline double f(double x) {
    return 4.0 / (1.0 + x * x);
}

// Последовательная версия — для замера T(1).
double integrate_serial(long nsteps, double a, double b) {
    const double dx = (b - a) / nsteps;
    double sum = 0.0;
    for (long i = 0; i < nsteps; ++i) {
        double x = a + (i + 0.5) * dx;     // середина i-го отрезка
        sum += f(x);
    }
    return sum * dx;
}

// Параллельная версия с локальной переменной и atomic-редукцией.
// Каждый поток копит СВОЮ локальную сумму (быстро, без синхронизации),
// в конце один раз атомарно прибавляет её к общей.
double integrate_omp(long nsteps, double a, double b) {
    const double dx = (b - a) / nsteps;
    double sum = 0.0;

    #pragma omp parallel
    {
        double local_sum = 0.0;            // ЛОКАЛЬНАЯ переменная (на поток)

        #pragma omp for schedule(static) nowait
        for (long i = 0; i < nsteps; ++i) {
            double x = a + (i + 0.5) * dx;
            local_sum += f(x);
        }

        #pragma omp atomic                 // безопасное сложение в общую sum
        sum += local_sum;
    }

    return sum * dx;
}

int main(int argc, char** argv) {
    long nsteps  = (argc > 1) ? std::atol(argv[1]) : 40000000L;
    int  repeats = (argc > 2) ? std::atoi(argv[2]) : 5;
    const double a = 0.0, b = 1.0;

    // Узнаём, сколько потоков нам выдали (для отчёта в выводе).
    int nthreads = 1;
    #pragma omp parallel
    {
        #pragma omp single
        nthreads = omp_get_num_threads();
    }

    // ----- Замер -----
    double best = 1e300;
    double result = 0.0;

    if (nthreads == 1) {
        // На одном потоке OpenMP всё равно создаёт «команду из одного»,
        // плюс atomic. Чтобы T(1) был честным baseline, на 1 потоке
        // используем чисто последовательную функцию.
        for (int r = 0; r < repeats; ++r) {
            auto t0 = std::chrono::high_resolution_clock::now();
            result = integrate_serial(nsteps, a, b);
            auto t1 = std::chrono::high_resolution_clock::now();
            double t = std::chrono::duration<double>(t1 - t0).count();
            if (t < best) best = t;
        }
    } else {
        for (int r = 0; r < repeats; ++r) {
            auto t0 = std::chrono::high_resolution_clock::now();
            result = integrate_omp(nsteps, a, b);
            auto t1 = std::chrono::high_resolution_clock::now();
            double t = std::chrono::duration<double>(t1 - t0).count();
            if (t < best) best = t;
        }
    }

    double err = std::fabs(result - M_PI);
    std::printf("threads=%d nsteps=%ld repeats=%d best_time=%.4f s "
                "result=%.10f err_vs_pi=%.2e\n",
                nthreads, nsteps, repeats, best, result, err);
    return 0;
}
