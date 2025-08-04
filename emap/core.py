from __future__ import annotations
from typing import Any, Iterable
import egglog


class Wire(egglog.Expr):
    @classmethod
    def from_input(cls, name: egglog.StringLike, index: egglog.i64Like) -> Wire:...

    @classmethod
    def from_const(cls, value: egglog.i64Like) -> Wire: ...

    @classmethod
    def from_dff(cls, d: Wire) -> Wire: ...

    def __and__(self, other: Wire) -> Wire: ...

    def __or__(self, other: Wire) -> Wire: ...

    def __xor__(self, other: Wire) -> Wire: ...

    def __invert__(self) -> Wire: ...

    @classmethod
    def mux(cls, a: Wire, b: Wire, s: Wire) -> Wire: ...


class WireVec(egglog.Expr):
    @classmethod
    def add(cls, a: egglog.Vec[Wire], b: egglog.Vec[Wire]) -> WireVec: ...

    @classmethod
    def sub(cls, a: egglog.Vec[Wire], b: egglog.Vec[Wire]) -> WireVec: ...

    @classmethod
    def mul(cls, a: egglog.Vec[Wire], b: egglog.Vec[Wire]) -> WireVec: ...

    def __getitem__(self, index: egglog.i64Like) -> Wire: ...


class width_of(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wv: WireVec, width: egglog.i64Like): ...


class Netlist(egglog.EGraph):
    _outputs: dict[tuple[str, int], Wire]
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
        if type_ in {"$and", "$or", "$xor", "$mux", "$add", "$sub", "$mul"}:
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
    def make_wirevec(type_: str, a: Iterable[Wire], b: Iterable[Wire]) -> WireVec:
        if type_ == "$add":
            return WireVec.add(egglog.Vec[Wire](*a), egglog.Vec[Wire](*b))
        if type_ == "$mul":
            return WireVec.mul(egglog.Vec[Wire](*a), egglog.Vec[Wire](*b))
        raise ValueError(f"Unsupported cell type: {type_}")

    def __init__(self, **egraph_kwargs):
        super().__init__(**egraph_kwargs)
        self._outputs = {}
        self._clk = None
        self._cnt = 0

    @property
    def auto_id(self) -> str:
        # generate a unique ID for each wire or wire vector
        self._cnt += 1
        return f"\\tmp{self._cnt}"

    def build_from_json(self, mod: dict, clk: str = "clk"):
        # NOTE: only support single global clock
        ports: dict[str, Any] = mod["ports"]
        cells: list[dict[str, Any]] = [cell for cell in mod["cells"].values()]
        wires: dict[int, Wire] = {}
        wire_from: dict[int, int | None] = {}  # maps wire index to cell index, None if the wire is a constant or input

        # build constants
        wires[-1] = self.let("x", Wire.from_const(-1))  # DC wire, represented as "x" in the netlist
        wires[0] = self.let("0", Wire.from_const(0))    # GND wire, represented as "0" in the netlist
        wires[1] = self.let("1", Wire.from_const(1))    # VCC wire, represented as "1" in the netlist
        wire_from.update({-1: None, 0: None, 1: None})  # map constants to None

        # build inputs
        for name, port in ports.items():
            direction, bits = port["direction"], port["bits"]
            if direction == "input":
                if name == clk:
                    if len(bits) != 1:
                        raise ValueError("Clock port must have exactly one bit")
                    self._clk = Netlist.bit_to_int(bits[0])
                for i, bit in enumerate(bits):
                    w = Netlist.bit_to_int(bit)
                    wires[w] = self.let(str(w), Wire.from_input(name, i))
                    wire_from[w] = None  # input wires are not connected to any cell
            elif direction != "output":
                raise ValueError(f"Unsupported port direction: {direction}")

        # TODO: build blackboxes' outputs

        # build dffs' q ports
        dffs: list[dict[str, Any]] = [cell for cell in cells if cell["type"] == "$dff"]
        for dff in dffs:
            conns, params = dff["connections"], dff["parameters"]
            if not self.param_to_int(params["CLK_POLARITY"]):
                raise ValueError("$dff with negative clock polarity is not supported")
            clk, q = conns["CLK"], conns["Q"]
            if len(clk) != 1 or Netlist.bit_to_int(clk[0]) != self._clk:
                raise ValueError(f"Clock {clk} does not match global clock {self._clk}")
            for wq in q:
                wq = Netlist.bit_to_int(wq)
                wires[wq] = self.let(str(wq), Wire.from_input(self.auto_id, 0)) # this is a placeholder, will be unioned later
                wire_from[wq] = None

        # build cells
        # NOTE: the cells may not be in topological order, so dfs is used to ensure all dependencies are resolved
        for i, cell in enumerate(cells):
            if cell["type"] != "$dff":
                wire_from.update((Netlist.bit_to_int(bit), i) for bit in Netlist.cell_to_outputs(cell))
        visited = set()
        def dfs(i: int | None):
            if i is None or i in visited:
                return
            cell = cells[i]
            type_, params, conns = cell["type"], cell["parameters"], cell["connections"]
            if type_ in {"$and", "$or", "$xor"}:    # bitwise logic gates, apply bitblast
                for wa, wb, wy in zip(conns["A"], conns["B"], conns["Y"]):
                    wa, wb, wy = Netlist.bit_to_int(wa), Netlist.bit_to_int(wb), Netlist.bit_to_int(wy)
                    dfs(wire_from[wa])
                    dfs(wire_from[wb])
                    wires[wy] = self.let(str(wy), Netlist.make_wire(type_, wires[wa], wires[wb]))
            elif type_ == "$not":
                a, y = conns["A"], conns["Y"]
                a, y = Netlist.bit_to_int(a[0]), Netlist.bit_to_int(y[0])
                dfs(wire_from[a])
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
                [dfs(wire_from[wa]) for wa in adjusted_a]
                [dfs(wire_from[wb]) for wb in adjusted_b]
                wvy = Netlist.make_wirevec(type_, (wires[wa] for wa in adjusted_a), (wires[wb] for wb in adjusted_b))
                for j, wy in enumerate(y):
                    wy = Netlist.bit_to_int(wy)
                    wires[wy] = self.let(str(wy), wvy[j])
            elif type_ == "$mux":
                # NOTE: it deserves considering whether it's a bitwise mux or a word-level mux
                # for me, I think it's better to treat it as bitwise
                a, b, s, y = conns["A"], conns["B"], conns["S"], conns["Y"]
                assert len(s) == 1, "Mux must have exactly one select bit"
                ws = Netlist.bit_to_int(s[0])
                dfs(wire_from[ws])  # dfs on select wire
                for wa, wb, wy in zip(a, b, y):
                    wa, wb, wy = Netlist.bit_to_int(wa), Netlist.bit_to_int(wb), Netlist.bit_to_int(wy)
                    dfs(wire_from[wa])
                    dfs(wire_from[wb])
                    wires[wy] = self.let(str(wy), Wire.mux(wires[wa], wires[wb], wires[ws]))
            elif type_ == "$dff":
                return
            else:
                attrs = cell["attributes"]
                if "module_not_derived" in attrs and self.param_to_int(attrs["module_not_derived"]):    # blackbox cell
                    raise RuntimeError("Blackbox cells are not supported")
                else:
                    raise ValueError(f"Unsupported cell type: {type_}")
            visited.add(i)

        # dfs from outputs
        for name, port in ports.items():
            direction, bits = port["direction"], port["bits"]
            if direction == "output":
                for i, bit in enumerate(bits):
                    w = Netlist.bit_to_int(bit)
                    dfs(wire_from[w])
                    self._outputs[(name, i)] = wires[w]

        # dfs from dffs' d ports
        for dff in dffs:
            conns = dff["connections"]
            for wd, wq in zip(conns["D"], conns["Q"]):
                wd, wq = Netlist.bit_to_int(wd), Netlist.bit_to_int(wq)
                dfs(wire_from[wd])
                # union dff's q port with from_dff(d port)
                self.register(egglog.union(wires[wq]).with_(Wire.from_dff(wires[wd])))
