#include <pybind11/pybind11.h>

#include "group_wires.h"
#include "group_wires_v2.h"
#include "prune_cells.h"
#include "build_and_sanitize_db.h"


PYBIND11_MODULE(emapcc, mod) {
    mod.def("group_wires", &emapcc::group_wires, "A C++ implementation of group_wires()");
    mod.def("group_wires_v2", &emapcc::group_wires_v2, "A C++ implementation of group_wires()");
    mod.def("prune_cells", &emapcc::prune_cells, "A C++ implementation of prune_cells()");
    mod.def("build_and_sanitize_db", &emapcc::build_and_sanitize_db, "A C++ implementation of build_and_sanitize_db()");
}
