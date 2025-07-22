#ifndef GROUP_WIRES_V2_H
#define GROUP_WIRES_V2_H

#include <pybind11/stl.h>


namespace emapcc {

std::pair<std::vector<std::vector<int>>, std::vector<std::vector<int>>> group_wires_v2(std::vector<std::set<int>> bundles);

}

#endif