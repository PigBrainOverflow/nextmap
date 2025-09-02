from __future__ import annotations
import egglog


class IdGen(egglog.Expr):
    def __init__(self, cur: egglog.i64Like): ...


class Wire(egglog.Expr):
    def __init__(self, id: egglog.i64Like): ...

    @classmethod
    def const(cls, value: egglog.StringLike) -> Wire: ...


class WireVec(egglog.Expr):
    def __init__(self, wires: egglog.Vec[Wire]): ...

    def __add__(self, other: WireVec) -> WireVec: ...

    def concat(self, other: WireVec) -> WireVec: ...


class WireSet(egglog.Expr):
    def __init__(self, wires: egglog.Set[Wire]): ...


class FromInput(egglog.Expr):
    def __init__(self, name: egglog.StringLike): ...


class AsOutput(egglog.Expr):
    def __init__(self, name: egglog.StringLike, wirevec: WireVec): ...
