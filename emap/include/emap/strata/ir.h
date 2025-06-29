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
};

// ops with a width
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
public:
    InstanceOp() = default;
    InstanceOp(std::string module_name) : module_name(std::move(module_name)) {}
    ~InstanceOp() = default;

    static void register_to(Dialect* dialect) { InstanceOp::dialect = dialect; }
    const Dialect* belong_to() const override { return InstanceOp::dialect; }
    const char* get_mnemonic() const override { return "instance"; }

private:
    std::string module_name; // name of the module this instance belongs to
    static Dialect* dialect;
};

class InputOp : public WireLikeOp {
public:
    // for external inputs
    InputOp(int width, std::string port_name)
        : width(width), instance(nullptr), port_name(std::move(port_name)) {}
    // for inputs from an instance
    InputOp(int width, InstanceOp* instance, std::string port_name)
        : width(width), instance(instance), port_name(std::move(port_name)) {}
    ~InputOp() = default;

    static void register_to(Dialect* dialect) { InputOp::dialect = dialect; }
    const Dialect* belong_to() const override { return InputOp::dialect; }
    const char* get_mnemonic() const override { return "input"; }

    int get_width() const override { return width; }

private:
    int width;
    InstanceOp* instance;  // the instance this input belongs to, nullptr if from external
    std::string port_name; // name of the port this input belongs to or itself if from external
    static Dialect* dialect;
};

class OutputOp : public WireLikeOp {
public:
    // for external outputs
    OutputOp(WireLikeOp* source, std::string port_name)
        : source(source), instance(nullptr), port_name(std::move(port_name)) {}
    // for outputs from an instance
    OutputOp(WireLikeOp* source, InstanceOp* instance, std::string port_name)
        : source(source), instance(instance), port_name(std::move(port_name)) {}
    ~OutputOp() = default;

    static void register_to(Dialect* dialect) { OutputOp::dialect = dialect; }
    const Dialect* belong_to() const override { return OutputOp::dialect; }
    const char* get_mnemonic() const override { return "output"; }

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

    int get_width() const override;

private:
    int width;        // -1 if not determined
    WireLikeOp* high; // msb
    WireLikeOp* low;  // lsb
    static Dialect* dialect;
};

class ExtractOp : public WireLikeOp {
public:
    // partial constructor
    ExtractOp()
        : data(nullptr), range(0, 0) {}
    ExtractOp(WireLikeOp* data, int low, int high)
        : data(data), range(low, high) {}
    ~ExtractOp() = default;

    static void register_to(Dialect* dialect) { ExtractOp::dialect = dialect; }
    const Dialect* belong_to() const override { return ExtractOp::dialect; }
    const char* get_mnemonic() const override { return "extract"; }

    int get_width() const override { return range.second - range.first + 1; }

private:
    // no need to buffer the width
    WireLikeOp* data;
    std::pair<int, int> range;  // (low, high) inclusive
    static Dialect* dialect;
};

class ConstOp : public WireLikeOp {
public:
    ConstOp() = default;
    ConstOp

    int get_width() const override { return bits.size(); }

private:
    // no need to buffer the width
    std::vector<Yosys::RTLIL::State> bits;
};

/*
 * Logic Dialect
 */
class AndOp : public Op {
public:
    AndOp() = default;
    ~AndOp() = default;

    static void register_to(Dialect* dialect) { AndOp::dialect = dialect; }
    const Dialect* belong_to() const override { return AndOp::dialect; }
    const char* get_mnemonic() const override { return "and"; }

private:
    static Dialect* dialect;
};

class OrOp : public Op {
public:
    OrOp() = default;
    ~OrOp() = default;

    static void register_to(Dialect* dialect) { OrOp::dialect = dialect; }
    const Dialect* belong_to() const override { return OrOp::dialect; }
    const char* get_mnemonic() const override { return "or"; }

private:
    static Dialect* dialect;
};

class Instance : public Serializable<json11::Json> {
public:
    Instance(std::string module_name) : module_name(std::move(module_name)) {}

private:
    std::string module_name;
};

class Module : public Serializable<json11::Json> {
public:
    Module(std::string name) : name(std::move(name)) {}
    Module(const json11::Json& module_json);          // build from JSON
    Module(const Yosys::RTLIL::Module* rtlil_module); // build from RTLIL
    ~Module();

    json11::Json serialize() const override;

private:
    std::string name;                         // module name
    std::map<std::string, InputOp*> inputs;   // port name -> input
    std::map<std::string, OutputOp*> outputs; // port name -> output
    std::set<std::unique_ptr<Op>> ops;        // set of ops in this module
};

class Design : public Serializable<json11::Json> {
public:
    Design(std::string name) : name(std::move(name)) {}
    Design(const json11::Json& design_json);
    ~Design() = default;

    json11::Json serialize() const override;
    void add_module(std::unique_ptr<Module> module);

private:
    std::string name;
    std::vector<std::unique_ptr<Module>> modules; // list of modules
};

}


#endif