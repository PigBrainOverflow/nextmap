#include <cassert>

#include "emap/serialization.h"


namespace emap::serialization {

Yosys::Json::array serialize(const Yosys::RTLIL::Design* design) {
    assert(design && "Design pointer cannot be nullptr");

    Yosys::Json::array design_json;
    for (const auto& [_, module] : design->modules_) {
        design_json.push_back(serialize(module));
    }
    return design_json;
};

Yosys::Json::object serialize(const Yosys::RTLIL::Module* module) {
    assert(module && "Module pointer cannot be nullptr");

    Yosys::Json::array wires_json, cells_json, conns_json;
    for (const auto& [_, wire] : module->wires_) {
        wires_json.push_back(serialize(wire));
    }
    for (const auto& [_, cell] : module->cells_) {
        cells_json.push_back(serialize(cell));
    }
    for (const auto& [sigl, sigr] : module->connections()) {
        conns_json.push_back(Yosys::Json::array{serialize(&sigl), serialize(&sigr)});
    }
    return json11::Json::object{
        {"wires", wires_json},
        {"cells", cells_json},
        {"connects", conns_json}
    };
}

Yosys::Json::object serialize(const Yosys::RTLIL::Wire* wire) {
    assert(wire && "Wire pointer cannot be nullptr");

    return json11::Json::object{
        {"name", wire->name.str()},
        {"width", wire->width},
        {"port_id", wire->port_id},
        {"port_input", wire->port_input},
        {"port_output", wire->port_output}
    };
}

Yosys::Json::object serialize(const Yosys::RTLIL::Cell* cell) {
    assert(cell && "Cell pointer cannot be nullptr");

    Yosys::Json::object params, conns;
    for (const auto& [name, value] : cell->parameters) {
        params.insert({name.str(), value.to_bits()});
    }
    for (const auto& [name, value] : cell->connections()) {
        conns.insert({name.str(), serialize(&value)});
    }
    return json11::Json::object{
        {"name", cell->name.str()},
        {"type", cell->type.str()},
        {"parameters", params},
        {"connects", conns}
    };
}

Yosys::Json::array serialize(const Yosys::RTLIL::SigSpec* sigspec) {
    assert(sigspec && "SigSpec pointer cannot be nullptr");

    Yosys::Json::array chunks;
    for (const auto& chunk : sigspec->chunks()) {
        if (chunk.is_wire()) {   // wire
            chunks.push_back(json11::Json::object{
                {"type", "wire"},
                {"name", chunk.wire->name.str()},
                {"offset", chunk.offset},
                {"width", chunk.width}
            });
        }
        else {    // constant
            chunks.push_back(json11::Json::object{
                {"type", "constant"},
                {"value", chunk.data},
                {"offset", chunk.offset},
                {"width", chunk.width}
            });
        }
    }
    return chunks;
}

}