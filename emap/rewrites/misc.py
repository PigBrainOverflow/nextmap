import egglog
from ..core import Wire, WireVec


class WireVecLength(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wirevec: WireVec, length: egglog.i64Like): ...  # (wirevec, length)

class WireVecEq(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, targets: egglog.Vec[Wire], index: egglog.i64Like, source: WireVec): ...

i = egglog.var("i", egglog.i64)
ws0 = egglog.var("ws0", egglog.Vec[Wire])
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)

misc_rules = egglog.ruleset(
    egglog.rule(WireVec(ws0)).then(WireVecLength(WireVec(ws0), ws0.length())),
    egglog.rule(WireVec.add(i, wv0, wv1)).then(WireVecLength(WireVec.add(i, wv0, wv1), i)),
    egglog.rule(WireVec.sub(i, wv0, wv1)).then(WireVecLength(WireVec.sub(i, wv0, wv1), i)),
    egglog.rule(WireVec.mul(i, wv0, wv1)).then(WireVecLength(WireVec.mul(i, wv0, wv1), i)),

    egglog.rewrite(WireVec(ws0)[i]).to(ws0[i]), # this can avoid recursion of indexing, e.g., WireVec([w0])[0] -> w0

    egglog.rule(    # base case for WireVecEq
        WireVec(ws0),   # we need this because we don't need to check those non-wirevec wires
        egglog.eq(ws0[0]).to(wv0[0]),
        WireVecLength(wv0, ws0.length()),
    ).then(WireVecEq(ws0, 1, wv0)),
    egglog.rule(    # inductive case for WireVecEq
        WireVecEq(ws0, i, wv0), i < ws0.length(),
        egglog.eq(ws0[i]).to(wv0[i])
    ).then(
        egglog.subsume(WireVecEq(ws0, i, wv0)),
        WireVecEq(ws0, i + 1, wv0)
    ),
    egglog.rule(    # termination case for WireVecEq
        WireVecEq(ws0, i, wv0), i >= ws0.length()
    ).then(egglog.union(WireVec(ws0)).with_(wv0))
)