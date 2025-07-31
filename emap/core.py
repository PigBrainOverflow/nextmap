from __future__ import annotations
from typing import Any
import egglog


class Wire(egglog.Expr):
    @classmethod
    def from_input(cls, name: egglog.StringLike) -> Wire: ...

    @classmethod
    def from_dff(cls, dff_q: Wire) -> Wire: ...

    def __and__(self, other: Wire) -> Wire: ...

    def __or__(self, other: Wire) -> Wire: ...

    def __xor__(self, other: Wire) -> Wire: ...

    def __invert__(self) -> Wire: ...

class WireVec(egglog.Expr):
    def __init__(self, vec: egglog.Vec[Wire]): ...

    @classmethod
    def add(cls, out_width: egglog.i64Like, a: WireVec, b: WireVec) -> WireVec: ...

    @classmethod
    def sub(cls, out_width: egglog.i64Like, a: WireVec, b: WireVec) -> WireVec: ...

    @classmethod
    def mul(cls, out_width: egglog.i64Like, a: WireVec, b: WireVec) -> WireVec: ...

    def __getitem__(self, index: egglog.i64Like) -> Wire: ...   # this is necessary for indexing from ops

class Netlist(egglog.EGraph):
    _outputs: dict[str, WireVec]    # TODO: use egglog relation instead?
    _clk: int | None
    _cnt: int

    @staticmethod
    def bit_to_int(bit: str | int) -> int:
        # DC is represented as "x" in the netlist, convert it to -1
        return -1 if bit == "x" else int(bit)

    @staticmethod
    def param_to_int(param: str | int) -> int:
        # param is either a binary string or an integer
        return param if isinstance(param, int) else int(param, base=2)

    @staticmethod
    def cell_to_outputs(cell: dict[str, Any]) -> list[str]:
        type_, conns = cell["type"], cell["connections"]
        if type_ in {"$and", "$or", "$xor"}:
            return conns["Y"]
        elif type_ in {"$add", "$mul"}:
            return conns["Y"]
        elif type_ == "$dff":
            return conns["Q"]
        return []

    @staticmethod
    def make_wire(type_: str, *inputs: Wire) -> Wire:
        if type_ == "$and":
            return inputs[0] & inputs[1]
        if type_ == "$or":
            return inputs[0] | inputs[1]
        if type_ == "$xor":
            return inputs[0] ^ inputs[1]
        if type_ == "$not":
            return ~inputs[0]
        raise ValueError(f"Unsupported cell type: {type_}")

    @staticmethod
    def make_wirevec(type_: str, out_width: int, *inputs: WireVec) -> WireVec:
        if type_ == "$add":
            return WireVec.add(out_width, inputs[0], inputs[1])
        if type_ == "$mul":
            return WireVec.mul(out_width, inputs[0], inputs[1])
        raise ValueError(f"Unsupported cell type: {type_}")

    @property
    def outputs(self) -> dict[str, WireVec]:
        return self._outputs

    def __init__(self, **egraph_kwargs):
        super().__init__(**egraph_kwargs)
        self._outputs = {}
        self._clk = None
        self._cnt = 0

    @property
    def auto_id(self) -> str:
        # generate a unique ID for each wire or wire vector
        self._cnt += 1
        return f"tmp{self._cnt}"

    def build_from_json(self, mod: dict, clk: str = "clk"):
        # NOTE: only support single global clock
        # NOTE: not support blackbox cells
        ports: dict[str, Any] = mod["ports"]
        cells: list[dict[str, Any]] = [cell for cell in mod["cells"].values()]
        wires: dict[int, Wire] = {}

        # build inputs
        for name, port in ports.items():
            direction, bits = port["direction"], port["bits"]
            if direction == "input":
                if name == clk:
                    if len(bits) != 1:
                        raise ValueError("Clock port must have exactly one bit")
                    self._clk = Netlist.bit_to_int(bits[0])
                wires.update((Netlist.bit_to_int(bit), self.let(f"{name}[{i}]", Wire.from_input(f"{name}[{i}]"))) for i, bit in enumerate(bits))

        # build consts
        wires[-1] = self.let("x", Wire.from_input("x")) # DC wire, represented as "x" in the netlist
        wires[0] = self.let("0", Wire.from_input("0"))  # GND wire, represented as "0" in the netlist
        wires[1] = self.let("1", Wire.from_input("1"))  # VCC wire, represented as "1" in the netlist

        # build cells
        # NOTE: the cells may not be in topological order, so dfs is used to ensure all dependencies are resolved
        wire_from: dict[int, int] = {}  # maps wire index to cell index
        for i, cell in enumerate(cells):
            wire_from.update((Netlist.bit_to_int(bit), i) for bit in Netlist.cell_to_outputs(cell))

        visited = set()
        def dfs(i: int):
            if i in visited:
                return
            cell = cells[i]
            type_, params, conns = cell["type"], cell["parameters"], cell["connections"]
            if type_ in {"$and", "$or", "$xor"}:    # bitwise logic gates, apply bitblast
                for wa, wb, wy in zip(conns["A"], conns["B"], conns["Y"]):
                    wa, wb, wy = Netlist.bit_to_int(wa), Netlist.bit_to_int(wb), Netlist.bit_to_int(wy)
                    if wa in wire_from: # not an input wire or const
                        dfs(wire_from[wa])
                    if wb in wire_from:
                        dfs(wire_from[wb])
                    if wy not in wires:
                        wires[wy] = self.let(str(wy), Netlist.make_wire(type_, wires[wa], wires[wb]))
            elif type_ == "$not":
                a, y = conns["A"], conns["Y"]
                a, y = Netlist.bit_to_int(a[0]), Netlist.bit_to_int(y[0])
                if a in wire_from:
                    dfs(wire_from[a])
                if y not in wires:
                    wires[y] = self.let(str(y), Netlist.make_wire(type_, wires[a]))
            elif type_ in {"$add", "$mul"}:  # word-level arithmetic operations
                # NOTE: it's hard to handle weird input widths, signed & unsigned, etc. in a generic way
                # NOTE: also it's hard to deal with different styles of extension, e.g., $signed(a) vs {16{a[15]}, a}
                a_signed, b_signed = Netlist.param_to_int(params["A_SIGNED"]), Netlist.param_to_int(params["B_SIGNED"])
                a, b, y = conns["A"], conns["B"], conns["Y"]
                if len(a) < len(y): # apply extension
                    adjusted_a = [Netlist.bit_to_int(bit) for bit in a] + [Netlist.bit_to_int(a[-1]) if a_signed else 0] * (len(y) - len(a))
                else:   # apply truncation if necessary
                    adjusted_a = [Netlist.bit_to_int(bit) for bit in a[:len(y)]]
                if len(b) < len(y): # apply extension
                    adjusted_b = [Netlist.bit_to_int(bit) for bit in b] + [Netlist.bit_to_int(b[-1]) if b_signed else 0] * (len(y) - len(b))
                else:   # apply truncation if necessary
                    adjusted_b = [Netlist.bit_to_int(bit) for bit in b[:len(y)]]
                [dfs(wire_from[wa]) for wa in adjusted_a if wa in wire_from]
                [dfs(wire_from[wb]) for wb in adjusted_b if wb in wire_from]
                wva = self.let(self.auto_id, WireVec(egglog.Vec(*(wires[wa] for wa in adjusted_a))))
                wvb = self.let(self.auto_id, WireVec(egglog.Vec(*(wires[wb] for wb in adjusted_b))))
                wvy = Netlist.make_wirevec(type_, len(y), wva, wvb)
                for j, wy in enumerate(y):
                    wy = Netlist.bit_to_int(wy)
                    if wy not in wires:
                        wires[wy] = self.let(str(wy), wvy[j])
            elif type_ == "$dff":
                if not self.param_to_int(params["CLK_POLARITY"]):
                    raise ValueError("$dff with negative clock polarity is not supported")
                d, clk, q = conns["D"], conns["CLK"], conns["Q"]
                if len(clk) != 1 or Netlist.bit_to_int(clk[0]) != self._clk:
                    raise ValueError(f"Clock {clk} does not match global clock {self._clk}")
                for wd, wq in zip(d, q):
                    wd, wq = Netlist.bit_to_int(wd), Netlist.bit_to_int(wq)
                    if wd in wire_from:
                        dfs(wire_from[wd])
                    if wq not in wires:
                        wires[wq] = self.let(str(wq), Wire.from_dff(wires[wd]))
            else:
                attrs = cell["attributes"]
                if "module_not_derived" in attrs and self.param_to_int(attrs["module_not_derived"]):    # blackbox cell
                    raise RuntimeError("Blackbox cells are not supported")
                else:
                    raise ValueError(f"Unsupported cell type: {type_}")
            visited.add(i)

        for i in range(len(cells)):
            dfs(i)

        # build outputs
        for name, port in ports.items():
            direction, bits = port["direction"], port["bits"]
            if direction == "output":
                self._outputs[name] = self.let(name, WireVec(egglog.Vec(*(wires[Netlist.bit_to_int(bit)] for bit in bits))))
