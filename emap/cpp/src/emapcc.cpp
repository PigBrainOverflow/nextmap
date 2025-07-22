#include <pybind11/pybind11.h>

#include "group_wires.h"
#include "group_wires_v2.h"


PYBIND11_MODULE(emapcc, mod) {
    mod.def("group_wires", &emapcc::group_wires, "A C++ implementation of group_wires()");
    mod.def("group_wires_v2", &emapcc::group_wires_v2, "A C++ implementation of group_wires()");
}
