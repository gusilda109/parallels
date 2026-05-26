// main.cu — заполнение массива синусами и суммирование на GPU
// Тип REAL задаётся на этапе сборки через -DUSE_DOUBLE=ON/OFF в CMake

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <chrono>
#include <cuda_runtime.h>

// ----- Тип элементов массива выбирается на этапе сборки -----
#ifdef USE_DOUBLE
    using REAL = double;
    #define REAL_NAME "double"
#else
    using REAL = float;
    #define REAL_NAME "float"
#endif

constexpr long long N = 10'000'000;          // 10^7 элементов
constexpr int       BLOCK = 256;             // нитей в блоке

// Двойная точность для константы π всегда — чтобы аргумент sin был максимально точным
constexpr double PI = 3.14159265358979323846;

// Удобный макрос для проверки ошибок CUDA
#define CUDA_CHECK(call)                                                       \
    do {                                                                       \
        cudaError_t err = (call);                                              \
        if (err != cudaSuccess) {                                              \
            fprintf(stderr, "CUDA error %s:%d: %s\n",                          \
                    __FILE__, __LINE__, cudaGetErrorString(err));              \
            std::exit(EXIT_FAILURE);                                           \
        }                                                                      \
    } while (0)

// --------------------------------------------------------------------
// Ядро 1: заполнение массива одним полным периодом синуса
//   data[i] = sin( 2*pi * i / N )
// --------------------------------------------------------------------
__global__ void fill_sine(REAL* data, long long n)
{
    long long idx = blockIdx.x * (long long)blockDim.x + threadIdx.x;
    if (idx >= n) return;

    // Считаем аргумент в double, потом приводим к REAL (важно для float-варианта)
    double arg = 2.0 * PI * (double)idx / (double)n;
    data[idx] = (REAL)sin(arg);
}

// --------------------------------------------------------------------
// Ядро 2: блочная редукция (сумма) с shared memory
// Каждый блок суммирует свой кусок и пишет частичную сумму в out[blockIdx.x]
// --------------------------------------------------------------------
__global__ void reduce_sum(const REAL* __restrict__ data, REAL* out, long long n)
{
    __shared__ REAL sdata[BLOCK];

    long long tid    = threadIdx.x;
    long long stride = (long long)blockDim.x * gridDim.x;
    long long i      = blockIdx.x * (long long)blockDim.x + threadIdx.x;

    // Grid-stride loop: накапливаем в локальной переменной — меньше обращений к shared
    REAL local = (REAL)0;
    while (i < n) {
        local += data[i];
        i += stride;
    }
    sdata[tid] = local;
    __syncthreads();

    // Древовидное сворачивание внутри блока
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) sdata[tid] += sdata[tid + s];
        __syncthreads();
    }

    if (tid == 0) out[blockIdx.x] = sdata[0];
}

int main()
{
    printf("=== Sine sum on GPU ===\n");
    printf("Element type : %s\n", REAL_NAME);
    printf("Array size N : %lld\n", N);
    printf("sizeof(REAL) : %zu bytes\n\n", sizeof(REAL));

    // ---- информация о GPU ----
    cudaDeviceProp prop{};
    CUDA_CHECK(cudaGetDeviceProperties(&prop, 0));
    printf("GPU: %s (CC %d.%d)\n\n", prop.name, prop.major, prop.minor);

    // ---- выделяем память на устройстве ----
    REAL* d_data = nullptr;
    CUDA_CHECK(cudaMalloc(&d_data, N * sizeof(REAL)));

    int grid = (int)((N + BLOCK - 1) / BLOCK);
    // Ограничиваем число блоков для редукции — каждому блоку всё равно достанется работы
    int reduce_grid = std::min(grid, 1024);

    REAL* d_partial = nullptr;
    CUDA_CHECK(cudaMalloc(&d_partial, reduce_grid * sizeof(REAL)));

    // ---- заполняем массив синусом ----
    auto t0 = std::chrono::high_resolution_clock::now();
    fill_sine<<<grid, BLOCK>>>(d_data, N);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    auto t1 = std::chrono::high_resolution_clock::now();

    // ---- суммируем на GPU ----
    reduce_sum<<<reduce_grid, BLOCK>>>(d_data, d_partial, N);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    auto t2 = std::chrono::high_resolution_clock::now();

    // ---- финальное досуммирование на CPU (всего reduce_grid элементов) ----
    REAL* h_partial = (REAL*)std::malloc(reduce_grid * sizeof(REAL));
    CUDA_CHECK(cudaMemcpy(h_partial, d_partial,
                          reduce_grid * sizeof(REAL),
                          cudaMemcpyDeviceToHost));

    REAL gpu_sum = (REAL)0;
    for (int i = 0; i < reduce_grid; ++i) gpu_sum += h_partial[i];

    auto ms_fill   = std::chrono::duration<double, std::milli>(t1 - t0).count();
    auto ms_reduce = std::chrono::duration<double, std::milli>(t2 - t1).count();

    // Аналитически сумма sin(2π·i/N) при i=0..N-1 равна 0
    // (это симметричная сумма по полному периоду)
    printf("Fill time    : %.3f ms\n", ms_fill);
    printf("Reduce time  : %.3f ms\n", ms_reduce);
    printf("\n--- RESULT ---\n");
    if (sizeof(REAL) == 8)
        printf("Sum (%s) = %.17e\n", REAL_NAME, (double)gpu_sum);
    else
        printf("Sum (%s)  = %.9e\n",  REAL_NAME, (double)gpu_sum);
    printf("Expected      = 0\n");

    std::free(h_partial);
    CUDA_CHECK(cudaFree(d_partial));
    CUDA_CHECK(cudaFree(d_data));
    return 0;
}
