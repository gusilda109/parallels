#include <iostream>
#include <iomanip>
#include <fstream>
#include <cstring>
#include <cmath>
#include <chrono>
#include <string>
#include <boost/program_options.hpp>

#ifndef STAGE
#define STAGE 5
#endif

#ifdef USE_NVTX
#include <nvtx3/nvToolsExt.h>
#define NVTX_PUSH(name) nvtxRangePushA(name)
#define NVTX_POP()      nvtxRangePop()
#else
#define NVTX_PUSH(name)
#define NVTX_POP()
#endif

namespace po = boost::program_options;

static const double TL = 10.0;
static const double TR = 20.0;
static const double BR = 30.0;
static const double BL = 20.0;

static void initialize(double* __restrict A, double* __restrict Anew, int n)
{
    std::memset(A,    0, sizeof(double) * n * n);
    std::memset(Anew, 0, sizeof(double) * n * n);

    for (int i = 0; i < n; ++i) {
        const double t = static_cast<double>(i) / (n - 1);
        const double top    = TL + (TR - TL) * t;
        const double bottom = BL + (BR - BL) * t;
        const double left   = TL + (BL - TL) * t;
        const double right  = TR + (BR - TR) * t;

        A[i]                 = top;     Anew[i]                 = top;
        A[(n - 1) * n + i]   = bottom;  Anew[(n - 1) * n + i]   = bottom;
        A[i * n]             = left;    Anew[i * n]             = left;
        A[i * n + (n - 1)]   = right;   Anew[i * n + (n - 1)]   = right;
    }
}

static void dump_matrix(const double* A, int n, std::ostream& os)
{
    os << std::fixed << std::setprecision(2);
    for (int j = 0; j < n; ++j) {
        for (int i = 0; i < n; ++i)
            os << std::setw(8) << A[j * n + i];
        os << '\n';
    }
}

int main(int argc, char** argv)
{
    int         n, iter_max, check;
    double      tol;
    bool        do_print;
    std::string out_file;

    po::options_description desc("Уравнение теплопроводности (OpenACC). Опции");
    desc.add_options()
        ("help,h",  "показать справку")
        ("grid,g",  po::value<int>(&n)->default_value(128),               "размер сетки N (сетка N x N)")
        ("tol,t",   po::value<double>(&tol)->default_value(1e-6),         "целевая точность")
        ("iters,i", po::value<int>(&iter_max)->default_value(1000000),    "макс. число итераций")
        ("check,c", po::value<int>(&check)->default_value(1),             "считать ошибку раз в N итераций (STAGE>=5)")
        ("print,p", po::bool_switch(&do_print)->default_value(false),     "вывести итоговую матрицу в терминал")
        ("out,o",   po::value<std::string>(&out_file)->default_value(""), "сохранить итоговую матрицу в файл");

    po::variables_map vm;
    try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);
    } catch (const std::exception& e) {
        std::cerr << "Ошибка аргументов: " << e.what() << "\n\n" << desc << '\n';
        return 1;
    }
    if (vm.count("help")) { std::cout << desc << '\n'; return 0; }
    if (n < 3)        { std::cerr << "grid должен быть >= 3\n"; return 1; }
    if (check < 1)    check = 1;

    const int size = n * n;
    double* A    = new double[size];
    double* Anew = new double[size];

    NVTX_PUSH("init");
    initialize(A, Anew, n);
    NVTX_POP();

    double error = 1.0;
    int    iter  = 0;

    const auto t_start = std::chrono::steady_clock::now();

#if STAGE >= 3
    #pragma acc data copyin(A[0:size], Anew[0:size])
#endif
    {
        NVTX_PUSH("solve");
        while (error > tol && iter < iter_max) {

#if STAGE == 1
            error = 0.0;
            #pragma acc kernels
            {
                for (int j = 1; j < n - 1; ++j)
                    for (int i = 1; i < n - 1; ++i) {
                        Anew[j*n + i] = 0.25 * ( A[j*n + i + 1] + A[j*n + i - 1]
                                               + A[(j-1)*n + i] + A[(j+1)*n + i] );
                        error = fmax(error, fabs(Anew[j*n + i] - A[j*n + i]));
                    }
                for (int j = 1; j < n - 1; ++j)
                    for (int i = 1; i < n - 1; ++i)
                        A[j*n + i] = Anew[j*n + i];
            }
            ++iter;

#elif STAGE == 2
            error = 0.0;
            #pragma acc parallel loop collapse(2) reduction(max:error)
            for (int j = 1; j < n - 1; ++j)
                for (int i = 1; i < n - 1; ++i) {
                    Anew[j*n + i] = 0.25 * ( A[j*n + i + 1] + A[j*n + i - 1]
                                           + A[(j-1)*n + i] + A[(j+1)*n + i] );
                    error = fmax(error, fabs(Anew[j*n + i] - A[j*n + i]));
                }
            #pragma acc parallel loop collapse(2)
            for (int j = 1; j < n - 1; ++j)
                for (int i = 1; i < n - 1; ++i)
                    A[j*n + i] = Anew[j*n + i];
            ++iter;

#elif STAGE == 3
            error = 0.0;
            #pragma acc parallel loop collapse(2) reduction(max:error) present(A[0:size], Anew[0:size])
            for (int j = 1; j < n - 1; ++j)
                for (int i = 1; i < n - 1; ++i) {
                    Anew[j*n + i] = 0.25 * ( A[j*n + i + 1] + A[j*n + i - 1]
                                           + A[(j-1)*n + i] + A[(j+1)*n + i] );
                    error = fmax(error, fabs(Anew[j*n + i] - A[j*n + i]));
                }
            #pragma acc parallel loop collapse(2) present(A[0:size], Anew[0:size])
            for (int j = 1; j < n - 1; ++j)
                for (int i = 1; i < n - 1; ++i)
                    A[j*n + i] = Anew[j*n + i];
            ++iter;

#elif STAGE == 4
            error = 0.0;
            #pragma acc parallel loop collapse(2) reduction(max:error) present(A[0:size], Anew[0:size])
            for (int j = 1; j < n - 1; ++j)
                for (int i = 1; i < n - 1; ++i) {
                    Anew[j*n + i] = 0.25 * ( A[j*n + i + 1] + A[j*n + i - 1]
                                           + A[(j-1)*n + i] + A[(j+1)*n + i] );
                    error = fmax(error, fabs(Anew[j*n + i] - A[j*n + i]));
                }
            { double* tmp = A; A = Anew; Anew = tmp; }
            ++iter;

#else
            const bool need_err = (iter % check == 0);
            if (need_err) {
                error = 0.0;
                #pragma acc parallel loop collapse(2) reduction(max:error) present(A[0:size], Anew[0:size])
                for (int j = 1; j < n - 1; ++j)
                    for (int i = 1; i < n - 1; ++i) {
                        Anew[j*n + i] = 0.25 * ( A[j*n + i + 1] + A[j*n + i - 1]
                                               + A[(j-1)*n + i] + A[(j+1)*n + i] );
                        error = fmax(error, fabs(Anew[j*n + i] - A[j*n + i]));
                    }
            } else {
                #pragma acc parallel loop collapse(2) present(A[0:size], Anew[0:size])
                for (int j = 1; j < n - 1; ++j)
                    for (int i = 1; i < n - 1; ++i)
                        Anew[j*n + i] = 0.25 * ( A[j*n + i + 1] + A[j*n + i - 1]
                                               + A[(j-1)*n + i] + A[(j+1)*n + i] );
            }
            { double* tmp = A; A = Anew; Anew = tmp; }
            ++iter;
#endif
        }
        NVTX_POP();

#if STAGE >= 3
        #pragma acc update self(A[0:size])
#endif
    }

    const auto t_end = std::chrono::steady_clock::now();
    const double seconds = std::chrono::duration<double>(t_end - t_start).count();

    std::cout << "Grid       : " << n << " x " << n << '\n'
              << "Stage      : " << STAGE << '\n'
              << "Iterations : " << iter  << '\n'
              << "Error      : " << std::scientific << std::setprecision(6) << error << '\n'
              << "Time, s    : " << std::fixed      << std::setprecision(6) << seconds << '\n';

    if (do_print) {
        std::cout << "\nИтоговая матрица " << n << "x" << n << ":\n";
        dump_matrix(A, n, std::cout);
    }
    if (!out_file.empty()) {
        std::ofstream f(out_file);
        if (f) { dump_matrix(A, n, f); std::cout << "Матрица сохранена в " << out_file << '\n'; }
        else   { std::cerr << "Не удалось открыть файл " << out_file << '\n'; }
    }

    delete[] A;
    delete[] Anew;
    return 0;
}