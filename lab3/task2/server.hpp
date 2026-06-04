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

    void start() {
        bool expected = false;
        if (!running_.compare_exchange_strong(expected, true)) {
            return;
        }
        stop_requested_ = false;
        worker_ = std::thread(&TaskServer::run, this);
    }

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

    T request_result(std::size_t id_res) {
        std::unique_lock<std::mutex> lock(results_mutex_);
        results_cv_.wait(lock, [&] {
            return results_.find(id_res) != results_.end();
        });
        return results_.at(id_res);
    }

    bool has_result(std::size_t id_res) {
        std::lock_guard<std::mutex> lock(results_mutex_);
        return results_.find(id_res) != results_.end();
    }

private:

    void run() {
        while (true) {
            std::pair<std::size_t, Task> item;
            {
                std::unique_lock<std::mutex> lock(queue_mutex_);
                queue_cv_.wait(lock, [&] {
                    return !queue_.empty() || stop_requested_;
                });
                if (queue_.empty() && stop_requested_) {
                    break;
                }
                item = std::move(queue_.front());
                queue_.pop();
            }

            T result = item.second();

            {
                std::lock_guard<std::mutex> lock(results_mutex_);
                results_.emplace(item.first, std::move(result));
            }
            results_cv_.notify_all();
        }
    }

    std::queue<std::pair<std::size_t, Task>> queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;

    std::unordered_map<std::size_t, T> results_;
    std::mutex results_mutex_;
    std::condition_variable results_cv_;

    std::thread worker_;
    std::atomic<bool> running_{false};
    bool stop_requested_ = false;
    std::size_t next_id_ = 0;
};

#endif