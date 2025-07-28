#ifndef GROUP_WIRES_V2_H
#define GROUP_WIRES_V2_H

#include <pybind11/stl.h>


namespace emapcc {

enum class CellType {
    And, Or, Xor
};

void build_and_sanitize_db(
    const std::vector<std::string>& cell_names,
    const std::vector<std::string>& wire_names,
    const std::vector<std::string>& logic_aby_cells,
    const std::vector<std::string>& muxes,
    const std::vector<std::string>& dffs
) {
    std::map<int, int> 
}

}

#endif