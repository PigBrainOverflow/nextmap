#include <pybind11/pybind11.h>

#include "group_wires.h"


PYBIND11_MODULE(emapcc, mod) {
    mod.def("group_wires", &emapcc::group_wires, "A C++ implementation of group_wires()");
}
