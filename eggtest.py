from __future__ import annotations

import egglog


egraph = egglog.EGraph()


class Dim(egglog.Expr):
    @egglog.method(egg_fn="Literal")
    def __init__(self, value: egglog.i64Like):
        ...

    @egglog.method(egg_fn="Named")
    @classmethod
    def named(cls, name: egglog.StringLike) -> Dim:
        ...

    @egglog.method(egg_fn="Mul")
    def __mul__(self, other: Dim) -> Dim:
        ...

a, b, c = egglog.vars_("a b c", Dim)
i, j = egglog.vars_("i j", egglog.i64)

egraph.register(
    egglog.rewrite(a * (b * c)).to((a * b) * c),
    egglog.rewrite((a * b) * c).to(a * (b * c)),
    egglog.rewrite(a * b).to(b * a),
    egglog.rewrite(Dim(i) * Dim(j)).to(Dim(i * j))
)

m = egraph.let("m", Dim.named("m"))
n = egraph.let("n", Dim.named("n"))
p = egraph.let("p", Dim.named("p"))

res = egraph.let("res", m * (n * p))

egraph.run(20)

egraph.display()