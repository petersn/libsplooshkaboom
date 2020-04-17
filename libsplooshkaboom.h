// C++ for Sploosh Kaboom.

#ifndef LIBSPLOOSHKABOOM_H
#define LIBSPLOOSHKABOOM_H

struct Results {
	std::vector<double> probabilities;
};

void initialize();

bool do_computation(
	Results& results,
	std::vector<int> hits,
	std::vector<int> misses,
	int squids_gotten
);

#endif

