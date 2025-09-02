from ..core import *


class UnionWire(egglog.Expr):   # intermediate relation
    def __init__(self, i: egglog.i64Like, vec0: egglog.Vec[Wire], vec1: egglog.Vec[Wire]): ...

wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)
vec0, vec1 = egglog.vars_("vec0 vec1", egglog.Vec[Wire])
i = egglog.var("i", egglog.i64)

wirevec_canonicalize_rules = egglog.ruleset(
    # basis
    egglog.rule(
        egglog.eq(WireVec(vec0)).to(WireVec(vec1)),
        egglog.ne(vec0).to(vec1)
    ).then(
        UnionWire(0, vec0, vec1),
        egglog.delete(WireVec(vec1))    # prevent re-matching
    ),

    # inductive
    egglog.rule(
        UnionWire(i, vec0, vec1),
        i < vec0.length(),
        i < vec1.length()
    ).then(
        egglog.union(vec0[i]).with_(vec1[i]),
        UnionWire(i + 1, vec0, vec1),
        egglog.delete(UnionWire(i, vec0, vec1))
    ),

    # final: clean up
    egglog.rule(
        UnionWire(i, vec0, vec1),
        i >= vec0.length()
    ).then(egglog.delete(UnionWire(i, vec0, vec1))),
    egglog.rule(
        UnionWire(i, vec0, vec1),
        i >= vec1.length()
    ).then(egglog.delete(UnionWire(i, vec0, vec1)))
)


wirevec_concat_rules = egglog.ruleset(
    egglog.rewrite(WireVec(vec0).concat(WireVec(vec1)), subsume=True).to(WireVec(vec0.append(vec1)))
)