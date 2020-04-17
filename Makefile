
CFLAGS=-Ofast -flto -g -fPIC -Wall -Wextra -Wpedantic -Wno-sign-compare `pkg-config --cflags --libs python2` -fdiagnostics-color
CXXFLAGS=$(CFLAGS) -std=c++17

all: _libsplooshkaboom.so

libsplooshkaboom_wrap.cxx: libsplooshkaboom.h libsplooshkaboom.i
	swig -c++ -python libsplooshkaboom.i

%.o: %.cxx
	$(CXX) -c $(CXXFLAGS) -o $@ $^

_libsplooshkaboom.so: libsplooshkaboom.o libsplooshkaboom_wrap.o
	$(CXX) -shared -Wl,-soname,$@ $(CXXFLAGS) -o $@ $^

search: search.o
	$(CXX) $(CXXFLAGS) -o $@ $^


.PHONY: clean
clean:
	rm -f *.o *.pyc libsplooshkaboom_wrap.cxx _libsplooshkaboom.so libsplooshkaboom.py

