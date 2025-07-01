#ifndef SERIALIZATION_H
#define SERIALIZATION_H

#include <kernel/json.h>


namespace emap::serialization {

Yosys::Json serialize(const Yosys::RTLIL::Module* module);


}


#endif