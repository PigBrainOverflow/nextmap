from __future__ import annotations


class Dialect:
    class Op:
        def __init__(self):
            pass

        def build(self, builder: Builder):
            pass


class Builder:
    _inputs: dict[]
    _wires: dict[Dialect.Op, str]
    _stmts: str

    def __init__(self):
        pass

    def clean(self):
        self._wire_decls.clear()


class BasicDialect(Dialect):
    PREFIX = "basic"

    def __init__(self):
        super().__init__()

    class InputOp(Dialect.Op):
        MNEMONIC = "input"
        _name: str
        _width: int

        def __init__(self, name: str, width: int):
            self._name = name
            self._width = width

    class OutputOp(Dialect.Op):
        MNEMONIC = "output"
        _name: str
        _data: Dialect.Op

        def __init__(self, name: str, data: Dialect.Op):
            self._name = name
            self._data = data

    class ConstOp(Dialect.Op):
        MNEMONIC = "const"
        _value: int

        def __init__(self, value: int):
            self._value = value

    class ConcatOp(Dialect.Op):
        MNEMONIC = "concat"
        _high: Dialect.Op
        _low: Dialect.Op

        def __init__(self, high: Dialect.Op, low: Dialect.Op):
            self._high = high
            self._low = low

    class ExtractOp(Dialect.Op):
        MNEMONIC = "extract"
        _operand: Dialect.Op
        _high: int
        _low: int

        def __init__(self, operand: Dialect.Op, high: int, low: int):
            self._operand = operand
            self._high = high
            self._low = low

    class DelayOp(Dialect.Op):
        # this will generate a latch
        # always @ (posedge clock)
        MNEMONIC = "delay"
        _clock: Dialect.Op
        _data: Dialect.Op

        def __init__(self, clock: Dialect.Op, data: Dialect.Op):
            self._clock = clock
            self._data = data


class LogicDialect(Dialect):
    PREFIX = "logic"

    def __init__(self):
        super().__init__()

    class AndOp(Dialect.Op):
        MNEMONIC = "and"
        _left: Dialect.Op
        _right: Dialect.Op

        def __init__(self, left: Dialect.Op, right: Dialect.Op):
            self._left = left
            self._right = right

    class OrOp(Dialect.Op):
        MNEMONIC = "or"
        _left: Dialect.Op
        _right: Dialect.Op

        def __init__(self, left: Dialect.Op, right: Dialect.Op):
            self._left = left
            self._right = right

    class NotOp(Dialect.Op):
        MNEMONIC = "not"
        _operand: Dialect.Op

        def __init__(self, operand: Dialect.Op):
            self._operand = operand


class ArithDialect(Dialect):
    PREFIX = "arith"

    def __init__(self):
        super().__init__()

    class AddOp(Dialect.Op):
        MNEMONIC = "add"
        _left: Dialect.Op
        _right: Dialect.Op

        def __init__(self, left: Dialect.Op, right: Dialect.Op):
            self._left = left
            self._right = right

    class SubOp(Dialect.Op):
        MNEMONIC = "sub"
        _left: Dialect.Op
        _right: Dialect.Op

        def __init__(self, left: Dialect.Op, right: Dialect.Op):
            self._left = left
            self._right = right

    class MulOp(Dialect.Op):
        MNEMONIC = "mul"
        _left: Dialect.Op
        _right: Dialect.Op

        def __init__(self, left: Dialect.Op, right: Dialect.Op):
            self._left = left
            self._right = right