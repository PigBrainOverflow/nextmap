import egglog
from ..core import Wire, WireVec


class WireVecLength(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wirevec: WireVec, length: egglog.i64Like): ...  # (wirevec, length)

i = egglog.var("i", egglog.i64)
ws0 = egglog.var("ws0", egglog.Vec[Wire])
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)

misc_rules = egglog.ruleset(
    egglog.rule(WireVec(ws0)).then(WireVecLength(WireVec(ws0), ws0.length())),
    egglog.rule(WireVec.add(i, wv0, wv1)).then(WireVecLength(WireVec.add(i, wv0, wv1), i)),

    egglog.rewrite(WireVec(ws0)[i]).to(ws0[i]), # this can avoid recursion of indexing, e.g., WireVec(WireVec([w0])[0])[0] -> WireVec([w0])[0] -> w0
    egglog.rule(
        egglog.eq(WireVec(ws0)).to()
    ).then()
)