#include <iostream>
#include <vector>
#include <cmath>

#ifdef USE_DOUBLE
using real_t = double;
#else
using real_t = float;
#endif

const size_t N = 10000000;

int main() {
    std::vector<real_t> data(N);

    for (size_t i = 0; i < N; ++i) {
        data[i] = std::sin(2.0 * M_PI * i / N);
    }


    real_t sum = 0;
    real_t c   = 0;
    for (size_t i = 0; i < N; ++i) {
        real_t y = data[i] - c;    
        real_t t = sum + y;   
        c = (t - sum) - y;        
        sum = t;                    
    }

    std::cout << "Sum: " << sum << std::endl;
    return 0;
}