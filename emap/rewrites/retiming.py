import egglog
from ..core import Wire, WireVec
from .misc import length_of


i = egglog.var("i", egglog.i64)
w0 = egglog.var("w0", Wire)
wv0, wv1, wv2 = egglog.vars_("wv0 wv1 wv2", WireVec)
ws0, ws1, ws2, ws3 = egglog.vars_("ws0 ws1 ws2 ws3", egglog.Vec[Wire])


# NOTE: run once
const_inputs_rules = egglog.ruleset(
    egglog.rewrite(Wire.from_input("x")).to(Wire.from_dff(Wire.from_input("x"))),
    egglog.rewrite(Wire.from_input("0")).to(Wire.from_dff(Wire.from_input("0"))),
    egglog.rewrite(Wire.from_input("1")).to(Wire.from_dff(Wire.from_input("1")))
)


# TODO: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class all_from_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, dff_qs: WireVec, dff_ds: egglog.Vec[Wire]): ...

# inductive rule for all_from_dffs
all_from_dffs_inductive_rule = egglog.rule(
    all_from_dffs(WireVec(ws0), ws1),
    ws0.length() > ws1.length(),
    egglog.eq(Wire.from_dff(w0)).to(ws0[ws1.length()])
).then(
    egglog.subsume(all_from_dffs(WireVec(ws0), ws1)),
    all_from_dffs(WireVec(ws0), ws1.push(w0))
)

# TODO: for now we only consider retiming for add, sub, and mul
# NOTE: these rules trigger all_from_dffs
all_from_dffs_base_rules = egglog.ruleset(
    egglog.rule(WireVec.add(i, wv0, wv1)).then(
        all_from_dffs(wv0, egglog.Vec[Wire]()),
        all_from_dffs(wv1, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.sub(i, wv0, wv1)).then(
        all_from_dffs(wv0, egglog.Vec[Wire]()),
        all_from_dffs(wv1, egglog.Vec[Wire]())
    ),
    egglog.rule(WireVec.mul(i, wv0, wv1)).then(
        all_from_dffs(wv0, egglog.Vec[Wire]()),
        all_from_dffs(wv1, egglog.Vec[Wire]())
    )
)


class union_vec_with_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, dff_qs: WireVec, dff_ds: WireVec, index: egglog.i64Like): ...    # index is decremented each step

# inductive rule for union_vec_with_dffs
union_vec_with_dffs_inductive_rule = egglog.rule(union_vec_with_dffs(wv0, wv1, i), i >= 0).then(
    egglog.subsume(union_vec_with_dffs(wv0, wv1, i)),
    egglog.union(wv0[i]).with_(Wire.from_dff(wv1[i])),
    union_vec_with_dffs(wv0, wv1, i - 1)
)


# NOTE: run once
arith_retiming_forward_rules = egglog.ruleset(
    egglog.rule(
        WireVec.add(i, wv0, wv1),
        all_from_dffs(wv0, ws0), ws0.length() >= i, # can be retimed
        all_from_dffs(wv1, ws1), ws1.length() >= i
    ).then(union_vec_with_dffs(WireVec.add(i, wv0, wv1), WireVec.add(i, WireVec(ws0), WireVec(ws1)), i - 1)),
    egglog.rule(
        WireVec.sub(i, wv0, wv1),
        all_from_dffs(wv0, ws0), ws0.length() >= i, # can be retimed
        all_from_dffs(wv1, ws1), ws1.length() >= i
    ).then(union_vec_with_dffs(WireVec.sub(i, wv0, wv1), WireVec.sub(i, WireVec(ws0), WireVec(ws1)), i - 1)),
    egglog.rule(
        WireVec.mul(i, wv0, wv1),
        all_from_dffs(wv0, ws0), ws0.length() >= i, # can be retimed
        all_from_dffs(wv1, ws1), ws1.length() >= i
    ).then(union_vec_with_dffs(WireVec.mul(i, wv0, wv1), WireVec.mul(i, WireVec(ws0), WireVec(ws1)), i - 1))
)


# TODO: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class all_to_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, dff_ds: WireVec, dff_qs: egglog.Vec[Wire]): ...

# inductive rule for all_to_dffs
all_to_dffs_inductive_rule = egglog.rule(
    all_to_dffs(wv0, ws0),
    length_of(wv0, i), i > ws0.length(),    # not finished yet
    egglog.eq(w0).to(Wire.from_dff(wv0[ws0.length()]))
).then(
    egglog.subsume(all_to_dffs(wv0, ws0)),
    all_to_dffs(wv0, ws0.push(w0))  # push a new dff q port
)

all_to_dffs_base_rules = egglog.ruleset(
    egglog.rule(egglog.eq(wv0).to(WireVec.add(i, wv1, wv2))).then(all_to_dffs(wv0, egglog.Vec[Wire]())),
    egglog.rule(egglog.eq(wv0).to(WireVec.sub(i, wv1, wv2))).then(all_to_dffs(wv0, egglog.Vec[Wire]())),
    egglog.rule(egglog.eq(wv0).to(WireVec.mul(i, wv1, wv2))).then(all_to_dffs(wv0, egglog.Vec[Wire]()))
)


class union_vec_with_vec(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, ws: egglog.Vec[Wire], wv: WireVec, index: egglog.i64Like): ...   # index is decremented each step

union_vec_with_vec_inductive_rule = egglog.rule(union_vec_with_vec(ws0, wv0, i), i >= 0).then(
    egglog.subsume(union_vec_with_vec(ws0, wv0, i)),
    egglog.union(ws0[i]).with_(wv0[i]),
    union_vec_with_vec(ws0, wv0, i - 1)
)


# NOTE: run once
arith_retiming_backward_rules = egglog.ruleset(
    egglog.rule(
        egglog.eq(wv0).to(WireVec.add(i, wv1, wv2)),
        all_to_dffs(wv0, ws0), ws0.length() >= i,  # can be retimed
    ).then(
        
    )
)


class BuildInputDffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, wirevec: WireVec, width: egglog.i64Like, dffs: egglog.Vec[Wire]): ...    # (original wirevec, total width, q wires)

class UnionOutputs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, targets: egglog.Vec[Wire], index: egglog.i64Like, source: WireVec): ...


retiming_rules = egglog.ruleset(

    # inductive case for BuildInputDffs
    egglog.rule(BuildInputDffs(wv0, i, ws0), ws0.length() < i).then(    # TODO: not sure whether we can subsume it
        egglog.subsume(BuildInputDffs(wv0, i, ws0)),
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