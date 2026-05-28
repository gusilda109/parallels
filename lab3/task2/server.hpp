// Task 2: сервер обработки задач, реализованный как шаблон класса.
//
// Сервер - отдельный поток, который берёт задачи из очереди, решает их
// (вызывая переданную функцию) и сохраняет результат в контейнер,
// откуда его можно быстро искать по id.
//
// Интерфейс по заданию:
//   void start()
//   void stop()
//   size_t add_task(task)            -> возвращает id задачи
//   T request_result(id_res)         -> возвращает результат (блокирующий вызов)
//
// Шаблонные параметры:
//   Task   - тип задачи (вызываемый объект без аргументов: () -> T)
//   T      - тип результата
//
// Выбор контейнера для результатов:
//   std::unordered_map<size_t, T>. Хэш-таблица даёт в среднем O(1) на
//   вставку и поиск по id. Удаление (если нужно забрать и стереть) тоже
//   в среднем O(1). Для нашего сценария "положил по id / нашёл по id" это
//   оптимальнее, чем дерево (map, O(log n)) или последовательный контейнер.

#ifndef TASK2_SERVER_HPP
#define TASK2_SERVER_HPP

#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <functional>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <thread>
#include <unordered_map>
#include <utility>

template <typename Task, typename T>
class TaskServer {
public:
    TaskServer() = default;

    ~TaskServer() {
        stop();
    }

    // Запустить сервер: поднять рабочий поток.
    void start() {
        bool expected = false;
        if (!running_.compare_exchange_strong(expected, true)) {
            return;  // уже запущен
        }
        stop_requested_ = false;
        worker_ = std::thread(&TaskServer::run, this);
    }

    // Остановить сервер: дообработать очередь, затем завершить поток.
    void stop() {
        if (!running_.load()) return;
        {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            stop_requested_ = true;
        }
        queue_cv_.notify_all();
        if (worker_.joinable()) {
            worker_.join();
        }
        running_.store(false);
    }

    // Добавить задачу в очередь. Возвращает уникальный id задачи.
    std::size_t add_task(Task task) {
        std::size_t id;
        {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            id = next_id_++;
            queue_.emplace(id, std::move(task));
        }
        queue_cv_.notify_one();
        return id;
    }

    // Запросить результат по id. Блокирующий вызов: ждёт, пока результат
    // не будет готов. Результат остаётся в контейнере (можно запросить
    // повторно); забрать с удалением можно через take_result.
    T request_result(std::size_t id_res) {
        std::unique_lock<std::mutex> lock(results_mutex_);
        results_cv_.wait(lock, [&] {
            return results_.find(id_res) != results_.end();
        });
        return results_.at(id_res);
    }

    // Неблокирующая проверка готовности результата.
    bool has_result(std::size_t id_res) {
        std::lock_guard<std::mutex> lock(results_mutex_);
        return results_.find(id_res) != results_.end();
    }

private:
    // Рабочий цикл потока сервера.
    void run() {
        while (true) {
            std::pair<std::size_t, Task> item;
            {
                std::unique_lock<std::mutex> lock(queue_mutex_);
                queue_cv_.wait(lock, [&] {
                    return !queue_.empty() || stop_requested_;
                });
                if (queue_.empty() && stop_requested_) {
                    break;  // очередь пуста и попросили остановиться
                }
                item = std::move(queue_.front());
                queue_.pop();
            }

            // Решаем задачу вне блокировок.
            T result = item.second();

            {
                std::lock_guard<std::mutex> lock(results_mutex_);
                results_.emplace(item.first, std::move(result));
            }
            results_cv_.notify_all();
        }
    }

    // --- Очередь задач ---
    std::queue<std::pair<std::size_t, Task>> queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;

    // --- Контейнер результатов (id -> результат) ---
    std::unordered_map<std::size_t, T> results_;
    std::mutex results_mutex_;
    std::condition_variable results_cv_;

    std::thread worker_;
    std::atomic<bool> running_{false};
    bool stop_requested_ = false;
    std::size_t next_id_ = 0;
};

#endif  // TASK2_SERVER_HPP
