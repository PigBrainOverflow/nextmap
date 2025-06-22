from __future__ import annotations


# base class for all dialects
class Dialect:
    pass


# base class for all operations
class Op:
    def build(self, builder: Builder):
        raise NotImplementedError

    def build_from_extract(self, builder: Builder, extract_op: Op):
        raise NotImplementedError


# base class for all builders
class Builder:
    def emit(self, *args) -> str:
        raise NotImplementedError

    def add_wire(self, op: Op, name: str | None = None, width: int = 1):
        raise NotImplementedError

    def get_wire(self, op: Op) -> tuple[str, int]:
        raise NotImplementedError

    def append_assign(self, assign: str):
        raise NotImplementedError


class BasicDialect(Dialect):
    PREFIX = "basic"

    def __init__(self):
        super().__init__()

    class InputOp(Op):
        MNEMONIC = "input"
        _name: str
        _width: int

        def __init__(self, name: str, width: int):
            self._name = name
            self._width = width

        def build(self, builder: Builder):
            builder.add_wire(self, f"{self._name}", self._width)

    class OutputOp(Op):
        MNEMONIC = "output"
        _name: str
        _data: Op

        def __init__(self, name: str, data: Op):
            self._name = name
            self._data = data

        def build(self, builder: Builder):
            self._data.build(builder)
            dname, dwidth = builder.get_wire(self._data)
            builder.add_wire(self, f"{self._name}", dwidth)
            builder.append_assign(f"{self._name} = {dname}")

    class ConstOp(Op):
        MNEMONIC = "const"
        _value: int

        def __init__(self, value: int):
            self._value = value

    class ConcatOp(Op):
        MNEMONIC = "concat"
        _high: Op
        _low: Op

        def __init__(self, high: Op, low: Op):
            self._high = high
            self._low = low

    class ExtractOp(Op):
        MNEMONIC = "extract"
        _data: Op
        _high: int
        _low: int

        def __init__(self, data: Op, high: int, low: int):
            self._data = data
            self._high = high
            self._low = low

        def build(self, builder: Builder):
            try:    # try build_from_extract first
                self._data.build_from_extract(builder, self)
            except NotImplementedError:
                # fallback to build
                self._data.build(builder)
                dname = builder.get_wire(self._data)[0]
                width = self._high - self._low + 1
                builder.add_wire(self, name=None, width=width)
                builder.append_assign(f"{builder.get_wire(self)[0]} = {dname}[{self._high}:{self._low}]")

    class DelayOp(Op):
        # this will generate a flip-flop without reset
        # always @ (posedge clock)
        MNEMONIC = "delay"
        _clock: Op
        _data: Op

        def __init__(self, clock: Op, data: Op):
            self._clock = clock
            self._data = data


class LogicDialect(Dialect):
    # bitwise logic operations
    PREFIX = "logic"

    def __init__(self):
        super().__init__()

    class AndOp(Op):
        MNEMONIC = "and"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            self._left = left
            self._right = right

    class OrOp(Op):
        MNEMONIC = "or"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            self._left = left
            self._right = right

    class NotOp(Op):
        MNEMONIC = "not"
        _operand: Op

        def __init__(self, operand: Op):
            self._operand = operand


class ArithDialect(Dialect):
    # unsigned integer arithmetic operations
    # must be connected to `basic.extract` to determine width
    PREFIX = "arith"

    def __init__(self):
        super().__init__()

    class AddOp(Op):
        MNEMONIC = "add"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            self._left = left
            self._right = right

    class SubOp(Op):
        MNEMONIC = "sub"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            self._left = left
            self._right = right

    class MulOp(Op):
        MNEMONIC = "mul"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            self._left = left
            self._right = right

        def build_from_extract(self, builder: Builder, extract_op: Op):
            if not isinstance(extract_op, BasicDialect.ExtractOp):
                raise NotImplementedError("MulOp can only be built from BasicDialect.ExtractOp.")
            if extract_op._low != 0 or extract_op._high < extract_op._low:
                raise ValueError("Extract operation must cover the full width of the multiplication result.")
            self._left.build(builder)
            self._right.build(builder)
            left_name = builder.get_wire(self._left)[0]
            right_name = builder.get_wire(self._right)[0]
            builder.add_wire(extract_op, name=None, width=extract_op._high + 1)
            builder.append_assign(f"{builder.get_wire(extract_op)[0]} = {left_name} * {right_name}")


class BehavioralVerilogBuilder(Builder):
    # only used to build modules
    _wires: dict[Op, tuple[str, int]]   # op to (name, width)
    _assigns: list[str]
    _counter: int

    def __init__(self):
        super().__init__()
        self._wires = {}
        self._assigns = []
        self._counter = 0

    def add_wire(self, op: Op, name: str | None = None, width: int = 1):
        if op in self._wires:
            raise ValueError(f"Wire for {op} already exists.")
        name = name or f"wire_{self._counter}"
        self._wires[op] = (name, width)

    def get_wire(self, op: Op) -> tuple[str, int]:
        if op not in self._wires:
            raise ValueError(f"Wire for {op} does not exist.")
        return self._wires[op]

    def append_assign(self, assign: str):
        self._assigns.append(assign)

    def emit(self, module_name: str) -> str:
        code = "/* Generated Module */\n"

        # module declaration
        code += f"module {module_name} (\n"
        for op, (name, width) in self._wires.items():
            if isinstance(op, BasicDialect.InputOp):
                code += f"    input [{width - 1}:0] {name},\n"
            elif isinstance(op, BasicDialect.OutputOp):
                code += f"    output [{width - 1}:0] {name},\n"
        code = code.rstrip(",\n") + "\n);\n\n"

        # wire declarations
        code += "    // wire declarations\n"
        for op, (name, width) in self._wires.items():
            if isinstance(op, BasicDialect.InputOp) or isinstance(op, BasicDialect.OutputOp):
                continue
            code += f"    wire [{width - 1}:0] {name};\n"
        code += "\n"

        # assign statements
        for assign in self._assigns:
            code += f"    assign {assign};\n"

        code += "\nendmodule\n"

        return code


if __name__ == "__main__":
    input_a = BasicDialect.InputOp("a", 8)
    input_b = BasicDialect.InputOp("b", 8)
    a_mul_b = BasicDialect.ExtractOp(ArithDialect.MulOp(input_a, input_b), high=15, low=0)
    output = BasicDialect.OutputOp("result", a_mul_b)

    builder = BehavioralVerilogBuilder()
    output.build(builder)
    code = builder.emit("multiplier")

    with open("multiplier.v", "w") as f:
        f.write(code)