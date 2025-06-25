from __future__ import annotations


# base class for all dialects
class Dialect:
    PREFIX: str


# base class for all operations
class Op:
    MNEMONIC: str

    def build(self, builder: Builder):
        raise NotImplementedError

    def build_from_extract(self, builder: Builder, extract_op: Op):
        raise NotImplementedError

    def __add__(self, other: Op) -> ArithDialect.AddOp:
        return ArithDialect.AddOp(self, other)

    def __sub__(self, other: Op) -> ArithDialect.SubOp:
        return ArithDialect.SubOp(self, other)

    def __mul__(self, other: Op) -> ArithDialect.MulOp:
        return ArithDialect.MulOp(self, other)

    def __getitem__(self, item: slice) -> BasicDialect.ExtractOp:
        # inclusive both start and stop
        # a[0:3] is equivalent to a[3:0] in Verilog
        if not isinstance(item, slice):
            raise TypeError("Indexing must be done with a slice.")
        if item.start is None or item.stop is None:
            raise ValueError("Slice must have both start and stop defined.")
        if item.start < 0 or item.stop < item.start:
            raise ValueError("Invalid slice range.")
        return BasicDialect.ExtractOp(self, item.stop, item.start)


class BinaryOp(Op):
    SYMBOL: str
    _left: Op
    _right: Op

    def __init__(self, left: Op, right: Op):
        self._left = left
        self._right = right


class UnaryOp(Op):
    SYMBOL: str
    _operand: Op

    def __init__(self, operand: Op):
        self._operand = operand


# base class for all builders
class Builder:
    def clear(self):
        raise NotImplementedError

    def emit(self, *args) -> str:
        raise NotImplementedError

    def add_wire(self, op: Op, name: str | None = None, width: int = 1):
        raise NotImplementedError

    def get_wire(self, op: Op) -> tuple[str, int]:
        raise NotImplementedError

    def has_wire(self, op: Op) -> bool:
        raise NotImplementedError

    def add_reg(self, width: int) -> str:
        raise NotImplementedError

    def append_assign(self, assign: str):
        raise NotImplementedError

    def append_proc(self, proc: str):
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

        @property
        def name(self) -> str:
            return self._name

        @property
        def width(self) -> int:
            return self._width

        def build(self, builder: Builder):
            if builder.has_wire(self):
                return
            builder.add_wire(self, f"{self._name}", self._width)

    class OutputOp(Op):
        MNEMONIC = "output"
        _name: str
        _data: Op
        _width: int | None

        def __init__(self, name: str, data: Op):
            self._name = name
            self._data = data
            self._width = None  # will be determined during build

        @property
        def name(self) -> str:
            return self._name

        @property
        def width(self) -> int | None:
            return self._width

        def build(self, builder: Builder):
            if builder.has_wire(self):
                return
            self._data.build(builder)
            dname, dwidth = builder.get_wire(self._data)
            self._width = dwidth
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
            if builder.has_wire(self):
                return
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
        # expressive enough to build any synchronous (re)set flip-flop
        MNEMONIC = "delay"
        _clock: Op
        _data: Op

        def __init__(self, clock: Op, data: Op):
            self._clock = clock
            self._data = data

        def build(self, builder: Builder):
            if builder.has_wire(self):
                return
            self._clock.build(builder)
            self._data.build(builder)
            dname, dwidth = builder.get_wire(self._data)
            rname = builder.add_reg(dwidth)
            builder.add_wire(self, name=None, width=dwidth)
            builder.append_assign(f"{builder.get_wire(self)[0]} = {rname}")
            builder.append_proc(f"{rname} <= {dname}")

    class MuxOp(Op):
        MNEMONIC = "mux"
        _selector: Op
        _true_case: Op
        _false_case: Op

        def __init__(self, selector: Op, true_case: Op, false_case: Op):
            self._selector = selector
            self._true_case = true_case
            self._false_case = false_case


class LogicDialect(Dialect):
    # bitwise logic operations
    PREFIX = "logic"

    def __init__(self):
        super().__init__()

    class AndOp(BinaryOp):
        MNEMONIC = "and"
        SYMBOL = "&"

        def __init__(self, left: Op, right: Op):
            super().__init__(left, right)

    class OrOp(BinaryOp):
        MNEMONIC = "or"
        SYMBOL = "|"

        def __init__(self, left: Op, right: Op):
            super().__init__(left, right)

    class NotOp(UnaryOp):
        MNEMONIC = "not"
        SYMBOL = "~"

        def __init__(self, operand: Op):
            super().__init__(operand)


class ArithDialect(Dialect):
    # unsigned integer arithmetic operations
    # must be connected to `basic.extract` to determine width
    PREFIX = "arith"

    def __init__(self):
        super().__init__()

    @staticmethod
    def _build_from_extract(op: BinaryOp, builder: Builder, extract_op: Op):
        if not isinstance(extract_op, BasicDialect.ExtractOp):
            raise NotImplementedError(f"{op.MNEMONIC} can only be built from BasicDialect.ExtractOp.")
        if extract_op._low != 0 or extract_op._high < extract_op._low:
            raise ValueError("Extract operation must cover the full width of the arithmetic result.")
        op._left.build(builder)
        op._right.build(builder)
        left_name = builder.get_wire(op._left)[0]
        right_name = builder.get_wire(op._right)[0]
        builder.add_wire(extract_op, name=None, width=extract_op._high + 1)
        builder.append_assign(f"{builder.get_wire(extract_op)[0]} = {left_name} {op.SYMBOL} {right_name}")

    class AddOp(BinaryOp):
        MNEMONIC = "add"
        SYMBOL = "+"

        def __init__(self, left: Op, right: Op):
            super().__init__(left, right)

        def build_from_extract(self, builder: Builder, extract_op: Op):
            ArithDialect._build_from_extract(self, builder, extract_op)

    class SubOp(BinaryOp):
        MNEMONIC = "sub"
        SYMBOL = "-"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            super().__init__(left, right)

        def build_from_extract(self, builder: Builder, extract_op: Op):
            ArithDialect._build_from_extract(self, builder, extract_op)

    class MulOp(BinaryOp):
        MNEMONIC = "mul"
        SYMBOL = "*"
        _left: Op
        _right: Op

        def __init__(self, left: Op, right: Op):
            super().__init__(left, right)

        def build_from_extract(self, builder: Builder, extract_op: Op):
            ArithDialect._build_from_extract(self, builder, extract_op)


class BehavioralVerilogBuilder(Builder):
    # only used to build modules
    _wires: dict[Op, tuple[str, int]]   # op to (name, width)
    _regs: list[tuple[str, int]]  # (name, width)
    _assigns: list[str]
    _procs: list[str]
    _counter: int

    def __init__(self):
        super().__init__()
        self._wires = {}
        self._regs = []
        self._assigns = []
        self._procs = []
        self._counter = 0

    def clear(self):
        self._wires.clear()
        self._regs.clear()
        self._assigns.clear()
        self._procs.clear()
        self._counter = 0

    def add_wire(self, op: Op, name: str | None = None, width: int = 1):
        if op in self._wires:
            raise ValueError(f"Wire for {op} already exists.")
        if name is None:
            name = f"wire_{self._counter}"
            self._counter += 1
        self._wires[op] = (name, width)

    def get_wire(self, op: Op) -> tuple[str, int]:
        if op not in self._wires:
            raise ValueError(f"Wire for {op} does not exist.")
        return self._wires[op]

    def has_wire(self, op: Op) -> bool:
        return op in self._wires

    def add_reg(self, width: int) -> str:
        name = f"reg_{self._counter}"
        self._regs.append((name, width))
        self._counter += 1
        return name

    def append_assign(self, assign: str):
        self._assigns.append(assign)

    def append_proc(self, proc: str):
        self._procs.append(proc)

    def emit(self, module_name: str, clock_name: str | None = None) -> str:
        code = "/* Generated Module */\n"

        # module declaration
        code += f"module {module_name} (\n"
        for op, (name, width) in self._wires.items():
            if isinstance(op, BasicDialect.InputOp):
                if clock_name and name == clock_name:
                    code += f"    input {name},\n"
                else:
                    code += f"    input [{width - 1}:0] {name},\n"
            elif isinstance(op, BasicDialect.OutputOp):
                code += f"    output [{width - 1}:0] {name},\n"
        code = code.rstrip(",\n") + "\n);\n\n"

        # wire declarations
        code += "    // declarations\n"
        for op, (name, width) in self._wires.items():
            if isinstance(op, BasicDialect.InputOp) or isinstance(op, BasicDialect.OutputOp):
                continue
            code += f"    wire [{width - 1}:0] {name};\n"

        # reg declarations
        for name, width in self._regs:
            code += f"    reg [{width - 1}:0] {name};\n"

        # assign statements
        for assign in self._assigns:
            code += f"    assign {assign};\n"
        code += "\n"

        # proc blocks
        if self._procs:
            if not clock_name:
                raise ValueError("Clock name must be provided if there are procedural blocks.")
            code += f"    always @ (posedge {clock_name}) begin\n"
            for proc in self._procs:
                code += f"        {proc};\n"
            code += "    end\n\n"

        code += "endmodule\n"

        return code
