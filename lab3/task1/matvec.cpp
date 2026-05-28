// Task 1: многопоточное умножение матрицы на вектор (matrix-vector product)
// с параллельной инициализацией массивов.
//
// Сборка: см. CMakeLists.txt
// Запуск:  ./matvec <N> <num_threads> [pin]
//   N            - размер квадратной матрицы (N x N), элементы double
//   num_threads  - число потоков
//   pin          - необязательный флаг "pin": привязать потоки к ядрам (Linux)
//
// Программа печатает в stdout строку CSV: N,threads,time_seconds
// что удобно для последующей обработки скриптом и заполнения таблицы.

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#if defined(__linux__)
#include <pthread.h>
#include <sched.h>
#endif

namespace {

// Привязка текущего потока к конкретному ядру (CPU affinity).
// Работает только на Linux; на других платформах — заглушка.
void pin_thread_to_core(std::size_t core_id) {
#if defined(__linux__)
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
#else
    (void)core_id;
#endif
}

// Разбивает диапазон [0, total) на num_threads примерно равных частей и
// возвращает [begin, end) для потока thread_id.
struct Range {
    std::size_t begin;
    std::size_t end;
};

Range make_range(std::size_t total, std::size_t num_threads, std::size_t thread_id) {
    const std::size_t chunk = total / num_threads;
    const std::size_t rem = total % num_threads;
    // Первые rem потоков получают на один элемент больше.
    std::size_t begin = thread_id * chunk + std::min(thread_id, rem);
    std::size_t extra = (thread_id < rem) ? 1 : 0;
    std::size_t end = begin + chunk + extra;
    return {begin, end};
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <N> <num_threads> [pin]\n";
        return 1;
    }

    const std::size_t N = static_cast<std::size_t>(std::stoull(argv[1]));
    const std::size_t num_threads = static_cast<std::size_t>(std::stoull(argv[2]));
    const bool pin = (argc >= 4 && std::string(argv[3]) == "pin");

    if (N == 0 || num_threads == 0) {
        std::cerr << "N and num_threads must be > 0\n";
        return 1;
    }

    const unsigned hw = std::thread::hardware_concurrency();

    // Матрица A (N x N) хранится построчно в одном плоском массиве,
    // вектор x (N), результат y (N).
    std::vector<double> A(N * N);
    std::vector<double> x(N);
    std::vector<double> y(N);

    // --- Параллельная инициализация ---
    // Каждый поток инициализирует свой диапазон строк матрицы и
    // соответствующий кусок векторов. Это важно: на NUMA-системах
    // "первое касание" (first-touch) физически размещает память рядом
    // с тем ядром, которое её инициализировало.
    {
        std::vector<std::thread> init_threads;
        init_threads.reserve(num_threads);
        for (std::size_t t = 0; t < num_threads; ++t) {
            init_threads.emplace_back([&, t]() {
                if (pin && hw > 0) pin_thread_to_core(t % hw);
                Range r = make_range(N, num_threads, t);
                for (std::size_t i = r.begin; i < r.end; ++i) {
                    // Детерминированное заполнение, без RNG, чтобы инициализация
                    // сама не стала узким местом.
                    double* row = &A[i * N];
                    for (std::size_t j = 0; j < N; ++j) {
                        row[j] = 1.0 + (static_cast<double>((i + j) % 100)) * 0.01;
                    }
                    x[i] = 1.0 + static_cast<double>(i % 50) * 0.02;
                    y[i] = 0.0;
                }
            });
        }
        for (auto& th : init_threads) th.join();
    }

    // --- Параллельное умножение, замер времени ---
    auto worker = [&](std::size_t t) {
        if (pin && hw > 0) pin_thread_to_core(t % hw);
        Range r = make_range(N, num_threads, t);
        for (std::size_t i = r.begin; i < r.end; ++i) {
            const double* row = &A[i * N];
            double sum = 0.0;
            for (std::size_t j = 0; j < N; ++j) {
                sum += row[j] * x[j];
            }
            y[i] = sum;
        }
    };

    const auto start = std::chrono::steady_clock::now();
    {
        std::vector<std::thread> threads;
        threads.reserve(num_threads);
        for (std::size_t t = 0; t < num_threads; ++t) {
            threads.emplace_back(worker, t);
        }
        for (auto& th : threads) th.join();
    }
    const auto finish = std::chrono::steady_clock::now();

    const double seconds =
        std::chrono::duration<double>(finish - start).count();

    // Контрольная сумма, чтобы компилятор не выкинул вычисления как мёртвый код.
    double checksum = 0.0;
    for (std::size_t i = 0; i < N; i += std::max<std::size_t>(1, N / 1000)) {
        checksum += y[i];
    }

    // CSV в stdout: N,threads,time. Диагностика — в stderr.
    std::cout << N << "," << num_threads << "," << seconds << "\n";
    std::cerr << "checksum=" << checksum << " pinned=" << (pin ? 1 : 0)
              << " hw_concurrency=" << hw << "\n";

    return 0;
}
