import egglog
from ..core import Wire, WireVec


class length_of(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wirevec: WireVec, length: egglog.i64Like): ...  # (wirevec, length)

class wv_eq(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, targets: egglog.Vec[Wire], index: egglog.i64Like, source: WireVec): ...

i, j = egglog.vars_("i j", egglog.i64)
ws0 = egglog.var("ws0", egglog.Vec[Wire])
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)

misc_rules = egglog.ruleset(
    egglog.rule(WireVec(ws0)).then(length_of(WireVec(ws0), ws0.length())),
    egglog.rule(WireVec.add(i, wv0, wv1)).then(length_of(WireVec.add(i, wv0, wv1), i)),
    egglog.rule(WireVec.sub(i, wv0, wv1)).then(length_of(WireVec.sub(i, wv0, wv1), i)),
    egglog.rule(WireVec.mul(i, wv0, wv1)).then(length_of(WireVec.mul(i, wv0, wv1), i)),

    egglog.rewrite(WireVec(ws0)[i]).to(ws0[i]), # this can avoid recursion of indexing, e.g., WireVec([w0])[0] -> w0

    # base case for wv_eq
    egglog.rule(
        WireVec(ws0),   # we need this because we don't need to check those non-wirevec wires
        egglog.eq(ws0[0]).to(wv0[0]),
        length_of(wv0, ws0.length()),
    ).then(wv_eq(ws0, 1, wv0)),
    # inductive case for wv_eq
    egglog.rule(
        wv_eq(ws0, i, wv0), i < ws0.length(),
        egglog.eq(ws0[i]).to(wv0[i])
    ).then(
        egglog.subsume(wv_eq(ws0, i, wv0)),
        wv_eq(ws0, i + 1, wv0)
    ),
    # termination case for wv_eq
    egglog.rule(wv_eq(ws0, i, wv0), i >= ws0.length()).then(egglog.union(WireVec(ws0)).with_(wv0)),

    # base case for zero_extended
    egglog.rule(WireVec.add(i, wv0, wv1)).then(
        egglog.union(wv0).with_(WireVec.zero_extended(i, wv0)),
        egglog.union(wv1).with_(WireVec.zero_extended(i, wv1))
    ),
    egglog.rule(WireVec.sub(i, wv0, wv1)).then(
        egglog.union(wv0).with_(WireVec.zero_extended(i, wv0)),
        egglog.union(wv1).with_(WireVec.zero_extended(i, wv1))
    ),
    egglog.rule(WireVec.mul(i, wv0, wv1)).then(
        egglog.union(wv0).with_(WireVec.zero_extended(i, wv0)),
        egglog.union(wv1).with_(WireVec.zero_extended(i, wv1))
    ),

    # inductive case for zero_extended
    egglog.rule(
        WireVec.zero_extended(i, WireVec(ws0)),
        egglog.eq(ws0[ws0.length() - 1]).to(Wire.from_input("0"))
    ).then(
        egglog.union(WireVec.zero_extended(i, WireVec(ws0))).with_(WireVec.zero_extended(i, WireVec(ws0.pop()))),
        egglog.subsume(WireVec.zero_extended(i, WireVec(ws0)))  # TODO: in almost all cases, we can subsume this because zero_extended is greedily matched
    )
)