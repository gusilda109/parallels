// Task 2: клиент-серверное приложение.
//
// Три клиента (каждый - отдельный поток), каждый добавляет N задач
// ОДНОГО типа:
//   client 1 -> sin(x),         x случайный
//   client 2 -> sqrt(x),        x случайный (>= 0)
//   client 3 -> pow(x, y),      x, y случайные
//
// Каждый клиент дожидается результатов и сохраняет их в свой файл в
// удобном для чтения/проверки виде. Формат строки результата:
//   <op> <arg1> [<arg2>] <result>
// Например:
//   sin 0.5234 0.499...
//   sqrt 4.0 2.0
//   pow 2.0 3.0 8.0
//
// Файлы потом читает и проверяет verify.cpp.

#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <thread>
#include <vector>

#include "server.hpp"

namespace {

// Тип результата - double для всех трёх задач.
using ResultT = double;

// Задача — std::function без аргументов, возвращающая double.
using TaskT = std::function<ResultT()>;

// Число задач на одного клиента (5 < N < 10000).
constexpr int N_TASKS = 2000;

// --- Шаблонные функции-задачи (как в методичке) ---
template <typename U>
U fun_sin(U arg) { return std::sin(arg); }

template <typename U>
U fun_sqrt(U arg) { return std::sqrt(arg); }

template <typename U>
U fun_pow(U x, U y) { return std::pow(x, y); }

// Клиент: добавляет N задач одного типа, ждёт результаты, пишет в файл.
// gen_task(rng, &arg1, &arg2, &has_two) формирует задачу и сохраняет
// её аргументы для записи в файл.
template <typename ServerT>
void run_client(ServerT& server,
                const std::string& op_name,
                const std::string& filename,
                unsigned seed,
                int n_tasks,
                bool two_args,
                std::function<ResultT(double, double)> compute) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(0.1, 10.0);

    std::vector<std::size_t> ids;
    std::vector<double> a1(n_tasks), a2(n_tasks);
    ids.reserve(n_tasks);

    for (int i = 0; i < n_tasks; ++i) {
        double x = dist(rng);
        double y = two_args ? dist(rng) : 0.0;
        a1[i] = x;
        a2[i] = y;
        // Захватываем аргументы по значению в задачу.
        TaskT task = [x, y, compute]() { return compute(x, y); };
        ids.push_back(server.add_task(std::move(task)));
    }

    // Дожидаемся результатов и пишем в файл.
    std::ofstream out(filename);
    out << std::setprecision(12);
    for (int i = 0; i < n_tasks; ++i) {
        ResultT res = server.request_result(ids[i]);
        if (two_args) {
            out << op_name << " " << a1[i] << " " << a2[i] << " " << res << "\n";
        } else {
            out << op_name << " " << a1[i] << " " << res << "\n";
        }
    }
}

}  // namespace

int main() {
    TaskServer<TaskT, ResultT> server;
    server.start();

    // Запускаем три клиента в отдельных потоках.
    std::thread c1(run_client<TaskServer<TaskT, ResultT>>,
                   std::ref(server), "sin", "results_sin.txt", 1u, N_TASKS, false,
                   std::function<ResultT(double, double)>(
                       [](double x, double) { return fun_sin(x); }));

    std::thread c2(run_client<TaskServer<TaskT, ResultT>>,
                   std::ref(server), "sqrt", "results_sqrt.txt", 2u, N_TASKS, false,
                   std::function<ResultT(double, double)>(
                       [](double x, double) { return fun_sqrt(x); }));

    std::thread c3(run_client<TaskServer<TaskT, ResultT>>,
                   std::ref(server), "pow", "results_pow.txt", 3u, N_TASKS, true,
                   std::function<ResultT(double, double)>(
                       [](double x, double y) { return fun_pow(x, y); }));

    c1.join();
    c2.join();
    c3.join();

    server.stop();

    std::cout << "Done. " << (3 * N_TASKS) << " tasks processed.\n"
              << "Files: results_sin.txt, results_sqrt.txt, results_pow.txt\n";
    return 0;
}
