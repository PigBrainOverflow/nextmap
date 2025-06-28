#include "emap/strata/ir.h"


namespace emap::strata {

Module::Module(const json11::Json& module_json)
: name(module_json["name"].string_value()) {
    std::map<int, void*> id_to_addr;

}

Module::Module(const Yosys::RTLIL::Module* rtlil_module) {}

Module::~Module() = default;

json11::Json Module::serialize() const {}

Design::Design(const json11::Json& design_json)
: name(design_json["name"].string_value()) {
    for (const auto& module_json : design_json["modules"].array_items()) {
        if (module_json.is_null()) {
            modules.push_back(nullptr);
        }
        else {
            modules.push_back(std::make_unique<Module>(module_json));
        }
    }
}

json11::Json Design::serialize() const {
    std::vector<json11::Json> module_jsons;
    for (const auto& module : modules) {
        if (module) {
            module_jsons.push_back(module->serialize());
        }
        else {
            module_jsons.push_back(json11::Json(nullptr));
        }
    }

    return json11::Json::object{
        {"name", name},
        {"modules", module_jsons}
    };
}

void Design::add_module(std::unique_ptr<Module> module) {
    modules.push_back(std::move(module));
}

}