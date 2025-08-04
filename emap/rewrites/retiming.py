from .common import *


# NOTE: run once
const_inputs_rules = egglog.ruleset(
    egglog.rewrite(Wire.from_input("x")).to(Wire.from_dff(Wire.from_input("x"))),
    egglog.rewrite(Wire.from_input("0")).to(Wire.from_dff(Wire.from_input("0"))),
    egglog.rewrite(Wire.from_input("1")).to(Wire.from_dff(Wire.from_input("1")))
)


# NOTE: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class all_from_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, qs: egglog.Vec[Wire], ds: egglog.Vec[Wire]): ...

# inductive rule for all_from_dffs
all_from_dffs_inductive_rule = egglog.rule(
    all_from_dffs(ws0, ws1),
    ws0.length() > ws1.length(),
    egglog.eq(Wire.from_dff(w0)).to(ws0[ws1.length()])
).then(
    egglog.subsume(all_from_dffs(ws0, ws1)),
    all_from_dffs(ws0, ws1.push(w0))
)

# TODO: for now we only consider retiming for add, sub, and mul
# NOTE: these rules trigger all_from_dffs
all_from_dffs_base_rules = egglog.ruleset(
    egglog.rule(WireVec.add(ws0, ws1)).then(
        all_from_dffs(ws0, egglog.Vec[Wire]()),
        all_from_dffs(ws1, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.sub(ws0, ws1)).then(
        all_from_dffs(ws0, egglog.Vec[Wire]()),
        all_from_dffs(ws1, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.mul(ws0, ws1)).then(
        all_from_dffs(ws0, egglog.Vec[Wire]()),
        all_from_dffs(ws1, egglog.Vec[Wire]())
    )
)