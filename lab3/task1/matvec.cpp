

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


struct Range {
    std::size_t begin;
    std::size_t end;
};

Range make_range(std::size_t total, std::size_t num_threads, std::size_t thread_id) {
    const std::size_t chunk = total / num_threads;
    const std::size_t rem = total % num_threads;
    std::size_t begin = thread_id * chunk + std::min(thread_id, rem);
    std::size_t extra = (thread_id < rem) ? 1 : 0;
    std::size_t end = begin + chunk + extra;
    return {begin, end};
}

} 

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

    std::vector<double> A(N * N);
    std::vector<double> x(N);
    std::vector<double> y(N);


    {
        std::vector<std::thread> init_threads;
        init_threads.reserve(num_threads);
        for (std::size_t t = 0; t < num_threads; ++t) {
            init_threads.emplace_back([&, t]() {
                if (pin && hw > 0) pin_thread_to_core(t % hw);
                Range r = make_range(N, num_threads, t);
                for (std::size_t i = r.begin; i < r.end; ++i) {
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

    double checksum = 0.0;
    for (std::size_t i = 0; i < N; i += std::max<std::size_t>(1, N / 1000)) {
        checksum += y[i];
    }

    std::cout << N << "," << num_threads << "," << seconds << "\n";
    std::cerr << "checksum=" << checksum << " pinned=" << (pin ? 1 : 0)
              << " hw_concurrency=" << hw << "\n";

    return 0;
}
