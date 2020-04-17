// C++ for Sploosh Kaboom.

#include <vector>
#include <iostream>
#include <sstream>
#include <fstream>
#include <cstdint>
#include <cassert>
#include "libsplooshkaboom.h"

template <typename T>
std::vector<T> slurp_path(std::string path) {
	std::ifstream t(path);
	std::stringstream buffer;
	buffer << t.rdbuf(); 
	std::string s = buffer.str();
	std::vector<T> result;
	for (int i = 0; i * sizeof(T) < s.size(); i++)
		result.push_back(((T*)s.data())[i]);
	return result;
}

struct PossibleBoard {
	uint64_t squids;
	uint64_t squid2;
	uint64_t squid3;
	uint64_t squid4;
	double probability;

	bool check_compatible(uint64_t hit_mask, uint64_t miss_mask, int squids_gotten) const {
		if (hit_mask & ~squids)
			return false;
		if (miss_mask & squids)
			return false;
		if (squids_gotten == -1)
			return true;
		int squids_hit = 0;
		squids_hit += (squid2 & ~hit_mask) == 0;
		squids_hit += (squid3 & ~hit_mask) == 0;
		squids_hit += (squid4 & ~hit_mask) == 0;
		return squids_hit == squids_gotten;
	}
};

std::vector<PossibleBoard> possible_boards;

struct SquidStartingDesc {
	int x, y;
	bool direction;
};

std::vector<SquidStartingDesc> starting_descs;

bool check_mask(uint64_t mask, int x, int y) {
	return mask & (1ull << (x + 8 * y));
}

bool check_desc_valid(
	uint64_t taken_so_far,
	const SquidStartingDesc& desc,
	int length,
	uint64_t* updated_taken_so_far=nullptr
) {
	for (int offset = 0; offset < length; offset++) {
		int nx = desc.x;
		int ny = desc.y;
		*(desc.direction ? &nx : &ny) += offset;
		uint64_t bit = 1ull << (nx + 8 * ny);
		if (nx > 7 or ny > 7 or (taken_so_far & bit))
			return false;
		taken_so_far |= bit;
	}
	if (updated_taken_so_far != nullptr)
		*updated_taken_so_far = taken_so_far;
	return true;
}

int count_valid_children(uint64_t taken_so_far, int length) {
	int children = 0;
	for (auto& desc : starting_descs)
		if (check_desc_valid(taken_so_far, desc, length, nullptr))
			children++;
	return children;
}

void initialize() {
	std::cout << "Initializing libsplooshkaboom." << std::endl;

	for (int y = 0; y < 8; y++)
		for (int x = 0; x < 8; x++)
			for (bool direction : {false, true})
				starting_descs.push_back({x, y, direction});

	// Count up the valid placements.
	uint64_t mask0 = 0;

	int64_t children0 = count_valid_children(mask0, 2);
	for (auto& squid2_desc : starting_descs) {
		uint64_t mask1;
		if (not check_desc_valid(mask0, squid2_desc, 2, &mask1))
			continue;

		int64_t children1 = count_valid_children(mask1, 3);
		for (auto& squid3_desc : starting_descs) {
			uint64_t mask2;
			if (not check_desc_valid(mask1, squid3_desc, 3, &mask2))
				continue;
	
			int64_t children2 = count_valid_children(mask2, 4);
			for (auto& squid4_desc : starting_descs) {
				uint64_t mask3;				
				if (not check_desc_valid(mask2, squid4_desc, 4, &mask3))
					continue;

				PossibleBoard pb;
				pb.squids = mask3;
				pb.squid2 = mask1;
				pb.squid3 = mask2 & ~mask1;
				pb.squid4 = mask3 & ~mask2;
				pb.probability = 1.0 / (children0 * children1 * children2);
				possible_boards.push_back(pb);
			}
		}
	}

	std::cout << "Possible boards found: " << possible_boards.size() << std::endl;
	double total_prob = 0;
	for (const PossibleBoard& pb : possible_boards) {
		assert(__builtin_popcountll(pb.squids) == 9);
		assert(__builtin_popcountll(pb.squid2) == 2);
		assert(__builtin_popcountll(pb.squid3) == 3);
		assert(__builtin_popcountll(pb.squid4) == 4);
		total_prob += pb.probability;
	}
	std::cout << "Total probability: " << total_prob << std::endl;
}

uint64_t make_mask(const std::vector<int>& bits) {
	uint64_t result = 0;
	for (int bit_index : bits)
		result |= 1ull << bit_index;
	return result;
}

bool do_computation(
	Results& results,
	std::vector<int> hits,
	std::vector<int> misses,
	int squids_gotten
) {
	uint64_t hit_mask = make_mask(hits);
	uint64_t miss_mask = make_mask(misses);

	double total_probability = 0;
	results.probabilities.clear();
	results.probabilities.resize(64, 0.0);
	for (const PossibleBoard& pb : possible_boards) {
		if (pb.check_compatible(hit_mask, miss_mask, squids_gotten)) {
			for (int bit_index = 0; bit_index < 64; bit_index++)
				if (pb.squids & (1ull << bit_index))
					results.probabilities[bit_index] += pb.probability;
			total_probability += pb.probability;
		}
	}
	if (total_probability == 0)
		return false;
	// Renormalize the distribution.
	for (int i = 0; i < 64; i++)
		results.probabilities[i] /= total_probability;
	return true;
}

