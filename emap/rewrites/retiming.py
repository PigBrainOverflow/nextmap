import egglog
from ..core import Wire, WireVec


# TODO: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class FromDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wires: egglog.Vec[Wire], dffs: egglog.Vec[Wire]): ...                    # (original wires, d wires)

class ToDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wirevec: WireVec, width: egglog.i64Like, dffs: egglog.Vec[Wire]): ...    # (original wirevec, total width, q wires)

class UnionOutputDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, target: WireVec, index: egglog.i64Like, source: WireVec): ...            # union target to the dffs of source at index

class BuildInputDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wirevec: WireVec, width: egglog.i64Like, dffs: egglog.Vec[Wire]): ...    # (original wirevec, total width, q wires)

class UnionOutputs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, target: egglog.Vec[Wire], index: egglog.i64Like, source: WireVec): ...

i = egglog.var("i", egglog.i64)
w0 = egglog.var("w0", Wire)
wv0, wv1, wv2 = egglog.vars_("wv0 wv1 wv2", WireVec)
ws0, ws1, ws2, ws3 = egglog.vars_("ws0 ws1 ws2 ws3", egglog.Vec[Wire])

retiming_rules = egglog.ruleset(
    # const inputs to const dffs
    egglog.rewrite(Wire.from_input("x")).to(Wire.from_dff(Wire.from_input("x"))),
    egglog.rewrite(Wire.from_input("0")).to(Wire.from_dff(Wire.from_input("0"))),
    egglog.rewrite(Wire.from_input("1")).to(Wire.from_dff(Wire.from_input("1"))),

    # inductive case for FromDffs
    egglog.rule(
        FromDffs(ws0, ws1),
        ws1.length() < ws0.length(),
        egglog.eq(Wire.from_dff(w0)).to(ws0[ws1.length()])
    ).then(
        egglog.subsume(FromDffs(ws0, ws1)),
        FromDffs(ws0, ws1.push(w0))
    ),

    # inductive case for ToDffs
    egglog.rule(
        ToDffs(wv0, i, ws0), ws0.length() < i,   # not finished yet
        egglog.eq(w0).to(wv0[i - 1])
    ).then(
        egglog.subsume(ToDffs(wv0, i, ws0)),
        ToDffs(wv0, i, ws0.push(w0))
    ),

    # inductive case for UnionOutputDffs
    egglog.rule(UnionOutputDffs(wv0, i, wv1), i >= 0).then(
        egglog.subsume(UnionOutputDffs(wv0, i, wv1)),
        egglog.union(wv0[i]).with_(Wire.from_dff(wv1[i])),
        UnionOutputDffs(wv0, i - 1, wv1)
    ),

    # TODO: for now we only consider retiming for add, sub, and mul
    # move dffs forward
    # base cases for FromDffs
    egglog.rule(WireVec.add(i, WireVec(ws0), WireVec(ws1))).then(
        FromDffs(ws0, egglog.Vec[Wire]()),
        FromDffs(ws1, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.sub(i, WireVec(ws0), WireVec(ws1))).then(
        FromDffs(ws0, egglog.Vec[Wire]()),
        FromDffs(ws1, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.mul(i, WireVec(ws0), WireVec(ws1))).then(
        FromDffs(ws0, egglog.Vec[Wire]()),
        FromDffs(ws1, egglog.Vec[Wire]())
    ),

    egglog.rule(    # can be retimed
        egglog.eq(wv0).to(WireVec.add(i, WireVec(ws0), WireVec(ws1))),
        FromDffs(ws0, ws2), ws2.length() >= i,
        FromDffs(ws1, ws3), ws3.length() >= i
    ).then(UnionOutputDffs(wv0, i - 1, WireVec.add(i, WireVec(ws2), WireVec(ws3)))),
    egglog.rule(    # can be retimed
        egglog.eq(wv0).to(WireVec.sub(i, WireVec(ws0), WireVec(ws1))),
        FromDffs(ws0, ws2), ws2.length() >= i,
        FromDffs(ws1, ws3), ws3.length() >= i
    ).then(UnionOutputDffs(wv0, i - 1, WireVec.sub(i, WireVec(ws2), WireVec(ws3)))),
    egglog.rule(    # can be retimed
        egglog.eq(wv0).to(WireVec.mul(i, WireVec(ws0), WireVec(ws1))),
        FromDffs(ws0, ws2), ws2.length() >= i,
        FromDffs(ws1, ws3), ws3.length() >= i
    ).then(UnionOutputDffs(wv0, i - 1, WireVec.mul(i, WireVec(ws2), WireVec(ws3)))),

    # TODO: for now we only consider retiming for add, sub, and mul
    # move dffs backward
    # base cases for ToDffs
    egglog.rule(egglog.eq(wv0).to(WireVec.add(i, wv1, wv2))).then(ToDffs(wv0, i, egglog.Vec[Wire]())),
    egglog.rule(egglog.eq(wv0).to(WireVec.sub(i, wv1, wv2))).then(ToDffs(wv0, i, egglog.Vec[Wire]())),
    egglog.rule(egglog.eq(wv0).to(WireVec.mul(i, wv1, wv2))).then(ToDffs(wv0, i, egglog.Vec[Wire]())),

    # inductive case for BuildInputDffs
    egglog.rule(BuildInputDffs(wv0, i, ws0), ws0.length() < i).then(    # TODO: not sure whether we can subsume it
        # egglog.subsume(BuildInputDffs(wv0, i, ws0)),
        BuildInputDffs(wv0, i, ws0.push(Wire.from_dff(wv0[ws0.length()])))
    ),

    # inductive case for UnionOutputs
    egglog.rule(UnionOutputs(ws0, i, wv0), i >= 0).then(
        egglog.subsume(UnionOutputs(ws0, i, wv0)),
        egglog.union(ws0[i]).with_(wv0[i]),
        UnionOutputs(ws0, i - 1, wv0)
    ),

    egglog.rule(    # can be retimed
        egglog.eq(wv0).to(WireVec.mul(i, wv1, wv2)),
        ToDffs(wv0, i, ws0), ws0.length() >= i
    ).then( # build input dffs
        BuildInputDffs(wv1, i, egglog.Vec[Wire]()),
        BuildInputDffs(wv2, i, egglog.Vec[Wire]())
    ),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.mul(i, wv1, wv2)),
        ToDffs(wv0, i, ws0), ws0.length() >= i,
        BuildInputDffs(wv1, i, ws1), ws1.length() >= i, # input dffs built
        BuildInputDffs(wv2, i, ws2), ws2.length() >= i
    ).then(UnionOutputs(ws0, i - 1, WireVec.mul(i, WireVec(ws1), WireVec(ws2))))
)