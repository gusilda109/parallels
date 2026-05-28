// Task 2: тест-проверка. Читает файлы с результатами, пересчитывает
// каждую операцию заново и сравнивает с записанным значением.
//
// Usage: ./verify
// Возвращает код 0 при успехе, 1 при наличии расхождений.

#include <cmath>
#include <fstream>
#include <iostream>
#include <string>

namespace {

constexpr double kEps = 1e-9;

bool almost_equal(double a, double b) {
    double diff = std::fabs(a - b);
    double scale = std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
    return diff <= kEps * scale;
}

// Проверка файла с одноаргументной операцией (sin/sqrt).
// Формат строки: <op> <arg> <result>
int check_one_arg(const std::string& file, double (*fn)(double)) {
    std::ifstream in(file);
    if (!in) {
        std::cerr << "Cannot open " << file << "\n";
        return -1;
    }
    std::string op;
    double arg, res;
    int lines = 0, bad = 0;
    while (in >> op >> arg >> res) {
        ++lines;
        if (!almost_equal(fn(arg), res)) {
            ++bad;
            if (bad <= 5)
                std::cerr << file << ": mismatch " << op << "(" << arg
                          << ")=" << res << " expected " << fn(arg) << "\n";
        }
    }
    std::cout << file << ": " << lines << " lines, " << bad << " mismatches\n";
    return bad;
}

// Проверка файла с двухаргументной операцией (pow).
// Формат строки: <op> <arg1> <arg2> <result>
int check_two_arg(const std::string& file, double (*fn)(double, double)) {
    std::ifstream in(file);
    if (!in) {
        std::cerr << "Cannot open " << file << "\n";
        return -1;
    }
    std::string op;
    double a, b, res;
    int lines = 0, bad = 0;
    while (in >> op >> a >> b >> res) {
        ++lines;
        if (!almost_equal(fn(a, b), res)) {
            ++bad;
            if (bad <= 5)
                std::cerr << file << ": mismatch " << op << "(" << a << "," << b
                          << ")=" << res << " expected " << fn(a, b) << "\n";
        }
    }
    std::cout << file << ": " << lines << " lines, " << bad << " mismatches\n";
    return bad;
}

}  // namespace

int main() {
    int total_bad = 0;
    int r;

    r = check_one_arg("results_sin.txt", [](double x) { return std::sin(x); });
    if (r < 0) return 1;
    total_bad += r;

    r = check_one_arg("results_sqrt.txt", [](double x) { return std::sqrt(x); });
    if (r < 0) return 1;
    total_bad += r;

    r = check_two_arg("results_pow.txt",
                      [](double x, double y) { return std::pow(x, y); });
    if (r < 0) return 1;
    total_bad += r;

    if (total_bad == 0) {
        std::cout << "ALL OK: results verified successfully.\n";
        return 0;
    }
    std::cout << "FAILED: " << total_bad << " mismatches total.\n";
    return 1;
}
