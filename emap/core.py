from __future__ import annotations
import egglog


class Wire(egglog.Expr):
    @classmethod
    def from_input(cls, name: egglog.StringLike) -> Wire: ...

    @egglog.method(egg_fn="&")
    def __and__(self, other: Wire) -> Wire: ...

    @egglog.method(egg_fn="|")
    def __or__(self, other: Wire) -> Wire: ...

    @egglog.method(egg_fn="^")
    def __xor__(self, other: Wire) -> Wire: ...

    @egglog.method(egg_fn="~")
    def __invert__(self) -> Wire: ...


class WireVec(egglog.Expr):
    @classmethod
    def from_wires(cls, wires: egglog.Vec[Wire]) -> WireVec: ...

    @egglog.method(egg_fn="[]")
    def extract(self, index: egglog.i64Like) -> Wire: ...

    @egglog.method(egg_fn="+")
    def add(self, other: WireVec) -> WireVec: ...

    @egglog.method(egg_fn="*")
    def mul(self, other: WireVec) -> WireVec: ...


egraph = egglog.EGraph()
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)
w0, w1 = egglog.vars_("w0 w1", Wire)

egraph.register(
    egglog.rewrite(w0 & w1).to(w1 & w0),
    egglog.rewrite(w0 | w1).to(w1 | w0),
    egglog.rewrite(w0 ^ w1).to(w1 ^ w0),
    egglog.rewrite(~~w0).to(w0),
)


ins0 = [egraph.let(f"ins0[{i}]", Wire.from_input(f"ins0[{i}]")) for i in range(4)]
ins1 = [egraph.let(f"ins1[{i}]", Wire.from_input(f"ins1[{i}]")) for i in range(4)]
# 4-bit adder example, use logic gates to compute the sum and carry
sum0 = egraph.let("sum0", ins0[0] ^ ins1[0])
carry0 = egraph.let("carry0", ins0[0] & ins1[0])
sum1 = egraph.let("sum1", sum0 ^ ins0[1] ^ ins1[1])
carry1 = egraph.let("carry1", (sum0 & (ins0[1] | ins1[1])) | carry0)
sum2 = egraph.let("sum2", sum1 ^ ins0[2] ^ ins1[2])
carry2 = egraph.let("carry2", (sum1 & (ins0[2] | ins1[2])) | carry1)
sum3 = egraph.let("sum3", sum2 ^ ins0[3] ^ ins1[3])
carry3 = egraph.let("carry3", (sum2 & (ins0[3] | ins1[3])) | carry2)

# add0 = egraph.let("add0", Add(WireVec.from_wires(egglog.Vec(ws[0], BitAnd(ws[5], ws[4]))), WireVec.from_wires(egglog.Vec(*ws[2:4]))))
# out0 = egraph.let("out0", add0.extract(egglog.i64(0)))
# out1 = egraph.let("out1", add0.extract(egglog.i64(1)))

# egraph.run(10)

egraph.display(graphviz=True)