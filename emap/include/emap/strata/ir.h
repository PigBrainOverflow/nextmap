#ifndef IR_H
#define IR_H

#include <vector>
#include <map>
#include <set>
#include <string>
#include <memory>
#include <kernel/rtlil.h>
#include <libs/json11/json11.hpp>

#include "emap/strata/serializable.h"


namespace emap::strata {

class Dialect {
public:
    Dialect(const char* prefix) : prefix(prefix) {}
    ~Dialect() = default;

    const char* get_prefix() const { return prefix; }

private:
    const char* prefix;
};

// base class for op
class Op : public Serializable<json11::Json> {
public:
    Op() = default;
    virtual ~Op() = default;

    virtual const Dialect* belong_to() const = 0;
    virtual const char* get_mnemonic() const = 0;

    virtual bool operator<(const Op& other) const = 0;
};

// op with a width
class WireLikeOp : public Op {
public:
    WireLikeOp() = default;
    virtual ~WireLikeOp() = default;

    virtual int get_width() const = 0;
};

/*
 * Basic Dialect
 */
class InstanceOp : public Op {
// referred by InputOp and OutputOp
public:
    InstanceOp() = default;
    InstanceOp(std::string module_name) : module_name(std::move(module_name)) {}
    ~InstanceOp() = default;

    static void register_to(Dialect* dialect) { InstanceOp::dialect = dialect; }
    const Dialect* belong_to() const override { return InstanceOp::dialect; }
    const char* get_mnemonic() const override { return "instance"; }

    bool operator<(const Op& other) const override;

private:
    std::string module_name; // name of the module this instance belongs to
    static Dialect* dialect;
};

class InputOp : public WireLikeOp {
public:
    InputOp(int width, std::string port_name, InstanceOp* instance = nullptr)
        : width(width), instance(instance), port_name(std::move(port_name)) {}
    ~InputOp() = default;

    static void register_to(Dialect* dialect) { InputOp::dialect = dialect; }
    const Dialect* belong_to() const override { return InputOp::dialect; }
    const char* get_mnemonic() const override { return "input"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return width; }

private:
    int width;
    InstanceOp* instance;  // the instance this input belongs to, nullptr if from external
    std::string port_name; // name of the port this input belongs to or itself if from external
    static Dialect* dialect;
};

class OutputOp : public WireLikeOp {
public:
    OutputOp(WireLikeOp* source, std::string port_name, InstanceOp* instance = nullptr)
        : source(source), instance(instance), port_name(std::move(port_name)) {}
    ~OutputOp() = default;

    static void register_to(Dialect* dialect) { OutputOp::dialect = dialect; }
    const Dialect* belong_to() const override { return OutputOp::dialect; }
    const char* get_mnemonic() const override { return "output"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return source->get_width(); }

private:
    // no need to buffer the width
    WireLikeOp* source;    // the source of this output
    InstanceOp* instance;  // the instance this output belongs to, nullptr if to external
    std::string port_name; // name of the port this output belongs to or itself if to external
    static Dialect* dialect;
};

class ConcatOp : public WireLikeOp {
public:
    // partial constructor
    ConcatOp(int width = -1)
        : width(width), high(nullptr), low(nullptr) {}
    ConcatOp(WireLikeOp* high, WireLikeOp* low)
        : width(high->get_width() + low->get_width()), high(high), low(low) {}
    ~ConcatOp() = default;

    static void register_to(Dialect* dialect) { ConcatOp::dialect = dialect; }
    const Dialect* belong_to() const override { return ConcatOp::dialect; }
    const char* get_mnemonic() const override { return "concat"; }

    bool operator<(const Op& other) const override;

    int get_width() const override;

private:
    mutable int width; // -1 if not determined
    WireLikeOp* high;  // msb
    WireLikeOp* low;   // lsb
    static Dialect* dialect;
};

class ExtractOp : public WireLikeOp {
public:
    ExtractOp(WireLikeOp* data = nullptr, int low = 0, int high = 0)
        : data(data), range(low, high) {}
    ~ExtractOp() = default;

    static void register_to(Dialect* dialect) { ExtractOp::dialect = dialect; }
    const Dialect* belong_to() const override { return ExtractOp::dialect; }
    const char* get_mnemonic() const override { return "extract"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return range.second - range.first + 1; }

private:
    // no need to buffer the width
    WireLikeOp* data;
    std::pair<int, int> range; // (low, high) inclusive
    static Dialect* dialect;
};

class ConstOp : public WireLikeOp {
public:
    ConstOp() = default;
    // construct from a bit
    ConstOp(Yosys::RTLIL::State bit) : bits{bit} {}
    // construct from an integer
    ConstOp(long long val, int width = 32);
    ~ConstOp() = default;

    static void register_to(Dialect* dialect) { ConstOp::dialect = dialect; }
    const Dialect* belong_to() const override { return ConstOp::dialect; }
    const char* get_mnemonic() const override { return "const"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return bits.size(); }

private:
    // no need to buffer the width
    std::vector<Yosys::RTLIL::State> bits;
    static Dialect* dialect;
};

/*
 * Logic Dialect
 */
class MuxOp : public WireLikeOp {
public:
    // partial constructor
    MuxOp(int width = -1)
        : width(width), selector(nullptr), true_case(nullptr), false_case(nullptr) {}
    MuxOp(WireLikeOp* selector, WireLikeOp* true_case, WireLikeOp* false_case)
        : width(true_case->get_width()), selector(selector), true_case(true_case), false_case(false_case) {}
    ~MuxOp() = default;

    static void register_to(Dialect* dialect) { MuxOp::dialect = dialect; }
    const Dialect* belong_to() const override { return MuxOp::dialect; }
    const char* get_mnemonic() const override { return "mux"; }

    bool operator<(const Op& other) const override;

    int get_width() const override;

private:
    mutable int width;
    WireLikeOp* selector;
    WireLikeOp* true_case;
    WireLikeOp* false_case;
    static Dialect* dialect;
};

class AndOp : public WireLikeOp {
public:
    // partial constructor
    AndOp(int width = -1)
        : width(width), left(nullptr), right(nullptr) {}
    AndOp(WireLikeOp* left, WireLikeOp* right)
        : width(left->get_width()), left(left), right(right) {}

    static void register_to(Dialect* dialect) { AndOp::dialect = dialect; }
    const Dialect* belong_to() const override { return AndOp::dialect; }
    const char* get_mnemonic() const override { return "and"; }

    bool operator<(const Op& other) const override;

    int get_width() const override;

private:
    mutable int width;
    WireLikeOp* left;  // left operand
    WireLikeOp* right; // right operand
    static Dialect* dialect;
};

/*
 * Arith Dialect
 */
class AddOp : public WireLikeOp {
// NOTE: width is forced not to be inferred
public:
    AddOp(int width, WireLikeOp* left = nullptr, WireLikeOp* right = nullptr)
        : width(width), left(left), right(right) {}
    ~AddOp() = default;

    static void register_to(Dialect* dialect) { AddOp::dialect = dialect; }
    const Dialect* belong_to() const override { return AddOp::dialect; }
    const char* get_mnemonic() const override { return "add"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return width; }

private:
    int width;
    WireLikeOp* left;  // left operand
    WireLikeOp* right; // right operand
    static Dialect* dialect;
};

class SubOp : public WireLikeOp {
// NOTE: width is forced not to be inferred
public:
    SubOp(int width, WireLikeOp* left = nullptr, WireLikeOp* right = nullptr)
        : width(width), left(left), right(right) {}
    ~SubOp() = default;

    static void register_to(Dialect* dialect) { SubOp::dialect = dialect; }
    const Dialect* belong_to() const override { return SubOp::dialect; }
    const char* get_mnemonic() const override { return "sub"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return width; }

private:
    int width;
    WireLikeOp* left;  // left operand
    WireLikeOp* right; // right operand
    static Dialect* dialect;
};

class MulOp : public WireLikeOp {
// NOTE: width is forced not to be inferred
public:
    MulOp(int width, WireLikeOp* left = nullptr, WireLikeOp* right = nullptr)
        : width(width), left(left), right(right) {}
    ~MulOp() = default;

    static void register_to(Dialect* dialect) { MulOp::dialect = dialect; }
    const Dialect* belong_to() const override { return MulOp::dialect; }
    const char* get_mnemonic() const override { return "mul"; }

    bool operator<(const Op& other) const override;

    int get_width() const override { return width; }

private:
    int width;
    WireLikeOp* left;  // left operand
    WireLikeOp* right; // right operand
    static Dialect* dialect;
};

/*
 * Module
 */
class Module : public Serializable<json11::Json> {
public:
    Module(const Yosys::RTLIL::Module* rtlil_module); // build from RTLIL
    ~Module() = default;

    json11::Json serialize() const override;

private:
    Op* get_op(std::unique_ptr<Op> op); // build op if not exists

    struct OpPtrLess {
        bool operator()(const std::unique_ptr<Op>& lhs, const std::unique_ptr<Op>& rhs) const;
    };

    std::string name;                             // module name
    std::map<std::string, InputOp*> inputs;       // port name -> input
    std::map<std::string, OutputOp*> outputs;     // port name -> output
    std::set<std::unique_ptr<Op>, OpPtrLess> ops; // set of ops in this module
};

}


#endif