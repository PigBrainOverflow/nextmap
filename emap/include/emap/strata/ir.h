#ifndef IR_H
#define IR_H

#include <string>
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
    Op(int id) : id(id) {}
    ~Op() = default;

    int get_id() const { return id; }
    virtual const Dialect* belong_to() const = 0;

private:
    int id;
};

/*
 * Basic Dialect
 */
class Input : public Op {
public:
    Input(int id) : Op(id) {}
    ~Input() = default;

    static void register_to(Dialect* dialect) { Input::dialect = dialect; }
    const Dialect* belong_to() const override { return Input::dialect; }

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

private:
    static Dialect* dialect;
};

class OrOp : public Op {
public:
    OrOp(int id) : Op(id) {}
    ~OrOp() = default;

    static void register_to(Dialect* dialect) { OrOp::dialect = dialect; }
    const Dialect* belong_to() const override { return OrOp::dialect; }

private:
    static Dialect* dialect;
};

}


#endif