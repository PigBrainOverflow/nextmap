from __future__ import annotations
from typing import Any
import egglog


class IdGen(egglog.Expr):
    def __init__(self, cur: egglog.i64Like): ...


class Wire(egglog.Expr):
    def __init__(self, id: egglog.i64Like): ...

    @classmethod
    def const(cls, value: egglog.StringLike) -> Wire: ...   # DC, GND, VCC

    def __and__(self, other: Wire) -> Wire: ...

    def __or__(self, other: Wire) -> Wire: ...

    def __xor__(self, other: Wire) -> Wire: ...

    def __invert__(self) -> Wire: ...

    @classmethod
    def mux(cls, a: Wire, b: Wire, s: Wire) -> Wire: ...


class WireVec(egglog.Expr):
    def __init__(self, wires: egglog.Vec[Wire]): ...

    @classmethod
    def from_input(cls, name: egglog.StringLike) -> WireVec: ...

    def __add__(self, other: WireVec) -> WireVec: ...

    def __sub__(self, other: WireVec) -> WireVec: ...

    def __mul__(self, other: WireVec) -> WireVec: ...

    def concat(self, other: WireVec) -> WireVec: ...

    def eq(self, other: WireVec) -> WireVec: ...

    def ne(self, other: WireVec) -> WireVec: ...

    def lt(self, other: WireVec) -> WireVec: ...

    def le(self, other: WireVec) -> WireVec: ...

    def gt(self, other: WireVec) -> WireVec: ...

    def ge(self, other: WireVec) -> WireVec: ...

    def logical_not(self) -> WireVec: ...

    def shl(self, other: WireVec) -> WireVec: ...

    def shr(self, other: WireVec) -> WireVec: ...

    def sshr(self, other: WireVec) -> WireVec: ...


class WireSet(egglog.Expr):
    def __init__(self, wires: egglog.Set[Wire]): ...

    def reduce_or(self) -> WireVec: ...

    def reduce_and(self) -> WireVec: ...


class AsOutput(egglog.Expr):
    def __init__(self, name: egglog.StringLike, wirevec: WireVec): ...


class Netlist(egglog.EGraph):
    _max_id: int
    _auto_id: int
    _idgen: IdGen | None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._max_id = 1
        self._auto_id = 0
        self._idgen = None

    @property
    def auto_id(self) -> int:
        self._auto_id += 1
        return self._auto_id

    def bit_to_wire(self, bit: int | str) -> Wire:
        if isinstance(bit, int):
            self._max_id = max(self._max_id, bit)
            return self.let(str(self.auto_id), Wire(bit))
        return self.let(str(self.auto_id), Wire.const(bit))

    def build_cell(self, type_: str, *args):
        # Arithmetic
        if type_ == "$add":
            self.register(egglog.union(args[0] + args[1]).with_(args[2]))
        elif type_ == "$sub":
            self.register(egglog.union(args[0] - args[1]).with_(args[2]))
        elif type_ == "$mul":
            self.register(egglog.union(args[0] * args[1]).with_(args[2]))
        # Logic
        elif type_ == "$and":
            self.register(egglog.union(args[0] & args[1]).with_(args[2]))
        elif type_ == "$or":
            self.register(egglog.union(args[0] | args[1]).with_(args[2]))
        elif type_ == "$xor":
            self.register(egglog.union(args[0] ^ args[1]).with_(args[2]))
        # Mux
        elif type_ == "$mux":
            self.register(egglog.union(Wire.mux(args[0], args[1], args[2])).with_(args[3]))
        # Comparison
        elif type_ == "$eq":
            self.register(egglog.union(args[0].eq(args[1])).with_(args[2]))
        elif type_ == "$ne":
            self.register(egglog.union(args[0].ne(args[1])).with_(args[2]))
        elif type_ == "$lt":
            self.register(egglog.union(args[0].lt(args[1])).with_(args[2]))
        elif type_ == "$le":
            self.register(egglog.union(args[0].le(args[1])).with_(args[2]))
        elif type_ == "$gt":
            self.register(egglog.union(args[0].gt(args[1])).with_(args[2]))
        elif type_ == "$ge":
            self.register(egglog.union(args[0].ge(args[1])).with_(args[2]))
        elif type_ == "$not":   # bitwise NOT
            self.register(egglog.union(~args[0]).with_(args[1]))
        elif type_ == "$logic_not":   # logical NOT
            self.register(egglog.union(args[0].logical_not()).with_(args[1]))
        elif type_ == "$reduce_or":
            self.register(egglog.union(args[0].reduce_or()).with_(args[1]))
        elif type_ == "$reduce_and":
            self.register(egglog.union(args[0].reduce_and()).with_(args[1]))
        # Shift
        elif type_ == "$shl":
            self.register(egglog.union(args[0].shl(args[1])).with_(args[2]))
        elif type_ == "$shr":
            self.register(egglog.union(args[0].shr(args[1])).with_(args[2]))
        elif type_ == "$sshr":
            self.register(egglog.union(args[0].sshr(args[1])).with_(args[2]))
        else:
            raise ValueError(f"Unknown cell type: {type_}")

    def build_from_json(self, mod: dict[str, Any]):
        # NOTE: For simplicity, we only consider combinational logic here.
        ports: dict[str, Any] = mod["ports"]
        cells: dict[str, Any] = mod["cells"]

        # build inputs & outputs
        for name, port in ports.items():
            direction, bits = port["direction"], port["bits"]
            wv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in bits))))
            if direction == "input":
                in_port = self.let(str(self.auto_id), WireVec.from_input(name))
                self.register(egglog.union(in_port).with_(wv))
            elif direction == "output":
                self.let(str(self.auto_id), AsOutput(name, wv))
            else:
                raise ValueError(f"Unknown port direction: {direction}")

        # build cells
        for name, cell in cells.items():
            type_, conns = cell["type"], cell["connections"]
            if type_ in {
                "$add", "$sub", "$mul",
                "$eq", "$ne", "$lt", "$le", "$gt", "$ge",
                "$shl", "$shr", "$sshr"
            }:
                abits, bbits, ybits = conns["A"], conns["B"], conns["Y"]
                awv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in abits))))
                bwv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in bbits))))
                ywv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in ybits))))
                self.build_cell(type_, awv, bwv, ywv)
            elif type_ in {"$and", "$or", "$xor"}:
                abits, bbits, ybits = conns["A"], conns["B"], conns["Y"]
                assert len(abits) == len(bbits) == len(ybits)
                for abit, bbit, ybit in zip(abits, bbits, ybits):
                    a = self.bit_to_wire(abit)
                    b = self.bit_to_wire(bbit)
                    y = self.bit_to_wire(ybit)
                    self.build_cell(type_, a, b, y)
            elif type_ == "$mux":
                abits, bbits, sbits, ybits = conns["A"], conns["B"], conns["S"], conns["Y"]
                assert len(abits) == len(bbits) == len(ybits)
                assert len(sbits) == 1
                s = self.bit_to_wire(sbits[0])
                for abit, bbit, ybit in zip(abits, bbits, ybits):
                    a = self.bit_to_wire(abit)
                    b = self.bit_to_wire(bbit)
                    y = self.bit_to_wire(ybit)
                    self.build_cell(type_, a, b, s, y)
            elif type_ == "$not":   # bitwise NOT
                abits, ybits = conns["A"], conns["Y"]
                assert len(abits) == len(ybits)
                for abit, ybit in zip(abits, ybits):
                    a = self.bit_to_wire(abit)
                    y = self.bit_to_wire(ybit)
                    self.build_cell(type_, a, y)
            elif type_ == "$logic_not":   # logical NOT
                abits, ybits = conns["A"], conns["Y"]
                awv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in abits))))
                ywv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in ybits))))
                self.build_cell(type_, awv, ywv)
            elif type_ in {"$reduce_or", "$reduce_and"}:
                abits, ybits = conns["A"], conns["Y"]
                awv = self.let(str(self.auto_id), WireSet(egglog.Set[Wire](*(self.bit_to_wire(bit) for bit in abits))))
                ywv = self.let(str(self.auto_id), WireVec(egglog.Vec[Wire](*(self.bit_to_wire(bit) for bit in ybits))))
                self.build_cell(type_, awv, ywv)
            elif type_ == "$scopeinfo":
                # ignore scope info
                continue
            else:
                raise ValueError(f"Unknown cell type: {type_}")

        self._idgen = self.let("idgen", IdGen(self._max_id))