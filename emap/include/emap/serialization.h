#ifndef SERIALIZATION_H
#define SERIALIZATION_H

#include <kernel/rtlil.h>
#include <kernel/json.h>


namespace emap::serialization {

Yosys::Json::array serialize(const Yosys::RTLIL::Design* design);
Yosys::Json::object serialize(const Yosys::RTLIL::Module* module);
Yosys::Json::object serialize(const Yosys::RTLIL::Wire* wire);
Yosys::Json::object serialize(const Yosys::RTLIL::Cell* cell);
Yosys::Json::array serialize(const Yosys::RTLIL::SigSpec* sigspec);

}


#endif