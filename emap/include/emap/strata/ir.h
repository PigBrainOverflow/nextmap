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
    Op(int id) : id(id) {}  // TODO: no need for id, use address to identify
    ~Op() = default;

    int get_id() const { return id; }
    virtual const Dialect* belong_to() const = 0;
    virtual const char* get_mnemonic() const = 0;

private:
    int id;
};

/*
 * Basic Dialect
 */
class InputOp : public Op {
public:
    InputOp(int id) : Op(id) {}
    ~InputOp() = default;

    static void register_to(Dialect* dialect) { InputOp::dialect = dialect; }
    const Dialect* belong_to() const override { return InputOp::dialect; }
    const char* get_mnemonic() const override { return "input"; }

private:
    static Dialect* dialect;
};

class OutputOp : public Op {
public:
    OutputOp(int id) : Op(id) {}
    ~OutputOp() = default;

    static void register_to(Dialect* dialect) { OutputOp::dialect = dialect; }
    const Dialect* belong_to() const override { return OutputOp::dialect; }
    const char* get_mnemonic() const override { return "output"; }

private:
    static Dialect* dialect;
};

/*
 * Logic Dialect
 */
class AndOp : public Op {
public:
    AndOp(int id) : Op(id) {}
    ~AndOp() = default;

    static void register_to(Dialect* dialect) { AndOp::dialect = dialect; }
    const Dialect* belong_to() const override { return AndOp::dialect; }
    const char* get_mnemonic() const override { return "and"; }

private:
    static Dialect* dialect;
};

class OrOp : public Op {
public:
    OrOp(int id) : Op(id) {}
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
    Module(const json11::Json& module_json);            // build from JSON
    Module(const Yosys::RTLIL::Module* rtlil_module);   // build from RTLIL module
    ~Module();

    json11::Json serialize() const override;

private:
    std::string name;                                   // module name
    std::map<std::string, InputOp*> inputs;             // port name -> input
    std::map<std::string, OutputOp*> outputs;           // port name -> output
    std::set<Op*> ops;                                  // set of ops in this module
    std::vector<std::unique_ptr<Instance>> instances;   // list of instances
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
    std::vector<std::unique_ptr<Module>> modules;  // list of modules
};

}


#endif