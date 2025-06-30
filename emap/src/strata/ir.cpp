#include <cassert>

#include "emap/strata/ir.h"


namespace emap::strata {

bool InstanceOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by address
    return this < &other;
}

bool InputOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_input = static_cast<const InputOp&>(other);
    // no need to compare width
    return std::tie(instance, port_name) < std::tie(other_input.instance, other_input.port_name);
}

bool OutputOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_output = static_cast<const OutputOp&>(other);
    return std::tie(instance, port_name, source) <
        std::tie(other_output.instance, other_output.port_name, other_output.source);
}

bool ConcatOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_concat = static_cast<const ConcatOp&>(other);
    // no need to compare width
    return std::tie(high, low) < std::tie(other_concat.high, other_concat.low);
}

bool ExtractOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_extract = static_cast<const ExtractOp&>(other);
    // no need to compare width
    return std::tie(data, range) < std::tie(other_extract.data, other_extract.range);
}

bool ConstOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // compare bits
    return bits < static_cast<const ConstOp&>(other).bits;
}

bool MuxOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_mux = static_cast<const MuxOp&>(other);
    // no need to compare width
    return std::tie(selector, true_case, false_case) <
           std::tie(other_mux.selector, other_mux.true_case, other_mux.false_case);
}

bool AndOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_and = static_cast<const AndOp&>(other);
    // no need to compare width
    return std::tie(left, right) < std::tie(other_and.left, other_and.right);
}

bool AddOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_add = static_cast<const AddOp&>(other);
    // no need to compare width
    return std::tie(left, right) < std::tie(other_add.left, other_add.right);
}

bool SubOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_sub = static_cast<const SubOp&>(other);
    // no need to compare width
    return std::tie(left, right) < std::tie(other_sub.left, other_sub.right);
}

bool MulOp::operator<(const Op& other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    const auto& other_mul = static_cast<const MulOp&>(other);
    // no need to compare width
    return std::tie(left, right) < std::tie(other_mul.left, other_mul.right);
}

bool ToClockOp::operator<(const Op &other) const {
    if (typeid(*this) != typeid(other)) {
        return typeid(*this).before(typeid(other));
    }
    // same type, compare by fields
    return signal < static_cast<const ToClockOp&>(other).signal;
}

int ConcatOp::get_width() const {
    if (width < 0 && high && low) {
        width = high->get_width() + low->get_width();
    }
    assert(width >= 0 && "Width of ConcatOp should be determined");
    return width;
}

int MuxOp::get_width() const {
    if (width < 0 && true_case && false_case) {
        width = true_case->get_width();
    }
    assert(width >= 0 && "Width of MuxOp should be determined");
    return width;
}

int AndOp::get_width() const {
    if (width < 0 && left && right) {
        width = left->get_width();
    }
    assert(width >= 0 && "Width of AndOp should be determined");
    return width;
}

int RegOp::get_width() const {
    if (width < 0 && data) {
        width = data->get_width();
    }
    assert(width >= 0 && "Width of RegOp should be determined");
    return width;
}

/*
 * Module
 */
json11::Json Module::serialize() const {
    json11::Json::object obj;
    obj["name"] = name;

    // serialize inputs
    json11::Json::array inputs_array;
    for (const auto& [port_name, input] : inputs) {
        inputs_array.push_back(json11::Json::object{
            {"port_name", port_name},
            {"width", input->get_width()}
        });
    }
    obj["inputs"] = inputs_array;

    // serialize outputs
    json11::Json::array outputs_array;
    for (const auto& [port_name, output] : outputs) {
        outputs_array.push_back(json11::Json::object{
            {"port_name", port_name},
            {"width", output->get_width()}
        });
    }
    obj["outputs"] = outputs_array;

    // TODO: serialize ops

    return json11::Json(obj);
}

Op* Module::get_op(std::unique_ptr<Op> op) {
    assert(op && "Cannot get null Op");
    auto it = ops.find(op);
    if (it != ops.end()) {
        return it->get();
    }
    // not found
    auto ret = op.get();
    ops.insert(std::move(op));
    return ret;
}

bool Module::OpPtrLess::operator()(const std::unique_ptr<Op>& lhs, const std::unique_ptr<Op>& rhs) const {
    assert(lhs && rhs && "Cannot compare null Op pointers");
    return *lhs < *rhs;
}

Module::Module(const Yosys::RTLIL::Module* rtlil_module) {
    assert(rtlil_module && "RTLIL module cannot be nullptr");

    name = rtlil_module->name.str();

    // build netlist

}

}