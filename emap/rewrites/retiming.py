import egglog
from ..core import Wire, WireVec


# TODO: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class FromDffs(egglog.Expr):
    def __init__(self, wires: egglog.Vec[Wire], index: egglog.i64, dffs: egglog.Vec[Wire]): ... # (original wires, current index, d wires)

i = egglog.var("i", egglog.i64)
w0 = egglog.var("w0", Wire)
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)
ws0, ws1 = egglog.vars_("ws0 ws1", egglog.Vec[Wire])

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
    )
)