CXX        ?= pgc++
OPT        ?= -O3 -fast
INFO       ?= -Minfo=all
BOOST_INC  ?=
BOOST_LIB  ?=
BOOST_LINK ?= -lboost_program_options

CXXFLAGS   = $(OPT) $(INFO) $(BOOST_INC)
LDFLAGS    = $(BOOST_LIB) $(BOOST_LINK)
SRC        = heat.cpp

.PHONY: all stages clean

all: heat_host heat_multicore heat_gpu

heat_host: $(SRC)
	$(CXX) -acc=host       $(CXXFLAGS) -o $@ $(SRC) $(LDFLAGS)

heat_multicore: $(SRC)
	$(CXX) -acc=multicore  $(CXXFLAGS) -o $@ $(SRC) $(LDFLAGS)

heat_gpu: $(SRC)
	$(CXX) -acc=gpu        $(CXXFLAGS) -o $@ $(SRC) $(LDFLAGS)

stages: heat_gpu_s1 heat_gpu_s2 heat_gpu_s3 heat_gpu_s4 heat_gpu_s5

heat_gpu_s%: $(SRC)
	$(CXX) -acc=gpu -DSTAGE=$* $(CXXFLAGS) -o $@ $(SRC) $(LDFLAGS)

clean:
	rm -f heat_host heat_multicore heat_gpu heat_gpu_s? *.qdrep *.nsys-rep *.sqlite