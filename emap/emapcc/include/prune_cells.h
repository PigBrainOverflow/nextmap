#ifndef PRUNE_CELLS_H
#define PRUNE_CELLS_H

#include <pybind11/stl.h>

#include "trie.h"


namespace emapcc {

std::set<int> prune_cells(const std::vector<std::tuple<float, std::vector<int>, std::vector<int>>>& cells);

}

#endif