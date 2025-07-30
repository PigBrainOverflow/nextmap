import egglog
from ..core import Wire, WireVec


# TODO: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class FromDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wires: egglog.Vec[Wire], index: egglog.i64Like, dffs: egglog.Vec[Wire]): ... # (original wires, current index, d wires)

class ToDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, target: WireVec, index: egglog.i64Like, source: WireVec): ...

i = egglog.var("i", egglog.i64)
w0 = egglog.var("w0", Wire)
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)
ws0, ws1, ws2, ws3 = egglog.vars_("ws0 ws1 ws2 ws3", egglog.Vec[Wire])

retiming_rules = egglog.ruleset(
    # retime const inputs to dffs
    egglog.rewrite(Wire.from_input("x")).to(Wire.from_dff(Wire.from_input("x"))),
    egglog.rewrite(Wire.from_input("0")).to(Wire.from_dff(Wire.from_input("0"))),
    egglog.rewrite(Wire.from_input("1")).to(Wire.from_dff(Wire.from_input("1"))),

    # TODO: for now we only consider retiming for add, sub, and mul
    egglog.rule(WireVec.add(i, WireVec(ws0), WireVec(ws1))).then(   # base case
        FromDffs(ws0, i, egglog.Vec[Wire]()),
        FromDffs(ws1, i, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.sub(i, WireVec(ws0), WireVec(ws1))).then(   # base case
        FromDffs(ws0, i, egglog.Vec[Wire]()),
        FromDffs(ws1, i, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.mul(i, WireVec(ws0), WireVec(ws1))).then(   # base case
        FromDffs(ws0, i, egglog.Vec[Wire]()),
        FromDffs(ws1, i, egglog.Vec[Wire]())
    ),
    egglog.rule(    # inductive case
        FromDffs(ws0, i, ws1),
        i > 0,
        egglog.eq(Wire.from_dff(w0)).to(ws0[i - 1])
    ).then(
        egglog.subsume(FromDffs(ws0, i, ws1)),
        FromDffs(ws0, i - 1, ws1.push(w0))
    ),

    # move dffs forward
    egglog.rule(
        egglog.eq(wv0).to(WireVec.add(i, WireVec(ws0), WireVec(ws1))),
        FromDffs(ws0, 0, ws2),
        FromDffs(ws1, 0, ws3)
    ).then(ToDffs(wv0, i - 1, WireVec.add(i, WireVec(ws2), WireVec(ws3)))),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.sub(i, WireVec(ws0), WireVec(ws1))),
        FromDffs(ws0, 0, ws2),
        FromDffs(ws1, 0, ws3)
    ).then(ToDffs(wv0, i - 1, WireVec.sub(i, WireVec(ws2), WireVec(ws3)))),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.mul(i, WireVec(ws0), WireVec(ws1))),
        FromDffs(ws0, 0, ws2),
        FromDffs(ws1, 0, ws3)
    ).then(ToDffs(wv0, i - 1, WireVec.mul(i, WireVec(ws2), WireVec(ws3)))),
    egglog.rule(
        ToDffs(wv0, i, wv1),
        i >= 0
    ).then(
        egglog.subsume(ToDffs(wv0, i, wv1)),
        egglog.union(wv0[i]).with_(Wire.from_dff(wv1[i])),
        ToDffs(wv0, i - 1, wv1)
    )
)