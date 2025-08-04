from .common import *


# NOTE: run once
const_inputs_rules = egglog.ruleset(
    egglog.rewrite(Wire.from_input("x")).to(Wire.from_dff(Wire.from_input("x"))),
    egglog.rewrite(Wire.from_input("0")).to(Wire.from_dff(Wire.from_input("0"))),
    egglog.rewrite(Wire.from_input("1")).to(Wire.from_dff(Wire.from_input("1")))
)


####################
# Retiming Forward #
####################
# NOTE: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class all_from_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, qs: egglog.Vec[Wire], ds: egglog.Vec[Wire]): ...

# iter rule for all_from_dffs
all_from_dffs_iter_rule = egglog.rule(
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

class union_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, qs: WireVec, ds: WireVec, index: egglog.i64Like): ...    # index is decremented each step

union_dffs_iter_rule = egglog.rule(union_dffs(wv0, wv1, i), i >= 0).then(
    egglog.subsume(union_dffs(wv0, wv1, i)),
    egglog.union(wv0[i]).with_(Wire.from_dff(wv1[i])),
    union_dffs(wv0, wv1, i - 1)
)

# NOTE: run once
arith_retiming_forward_rules = egglog.ruleset(
    egglog.rule(
        WireVec.add(ws0, ws1),
        all_from_dffs(ws0, ws2), ws2.length() >= ws0.length(),
        all_from_dffs(ws1, ws3), ws3.length() >= ws1.length()
    ).then(union_dffs(WireVec.add(ws0, ws1), WireVec.add(ws2, ws3), ws0.length() - 1)),
    egglog.rule(
        WireVec.sub(ws0, ws1),
        all_from_dffs(ws0, ws2), ws2.length() >= ws0.length(),
        all_from_dffs(ws1, ws3), ws3.length() >= ws1.length()
    ).then(union_dffs(WireVec.sub(ws0, ws1), WireVec.sub(ws2, ws3), ws0.length() - 1)),
    egglog.rule(
        WireVec.mul(ws0, ws1),
        all_from_dffs(ws0, ws2), ws2.length() >= ws0.length(),
        all_from_dffs(ws1, ws3), ws3.length() >= ws1.length()
    ).then(union_dffs(WireVec.mul(ws0, ws1), WireVec.mul(ws2, ws3), ws0.length() - 1))
)


#####################
# Retiming Backward #
#####################
"""
Typical Order:
all_to_dffs_base_rules -> all_to_dffs_iter_rule ->
arith_retiming_backward_start_rules -> build_dffs_iter_rule ->
arith_retiming_backward_end_rules -> union_dffs_iter_rule
"""
# TODO: egglog.Vec is not a syntactic sugar over list's cons and nil, for simplicity we use it but clearly list is more efficient here
class all_to_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, ds: WireVec, qs: egglog.Vec[Wire]): ...

# iter rule for all_to_dffs
all_to_dffs_iter_rule = egglog.rule(
    all_to_dffs(wv0, ws0), wv0.length() > ws0.length(),
    egglog.eq(w0).to(Wire.from_dff(wv0[ws0.length()]))
).then(
    egglog.subsume(all_to_dffs(wv0, ws0)),
    all_to_dffs(wv0, ws0.push(w0))  # push a new dff q port
)

all_to_dffs_base_rules = egglog.ruleset(
    egglog.rule(egglog.eq(wv0).to(WireVec.add(ws0, ws1))).then(all_to_dffs(wv0, egglog.Vec[Wire]())),
    egglog.rule(egglog.eq(wv0).to(WireVec.sub(ws0, ws1))).then(all_to_dffs(wv0, egglog.Vec[Wire]())),
    egglog.rule(egglog.eq(wv0).to(WireVec.mul(ws0, ws1))).then(all_to_dffs(wv0, egglog.Vec[Wire]()))
)

# class union_vec(egglog.Expr):
#     @egglog.method(unextractable=True)
#     def __init__(self, ws: egglog.Vec[Wire], wv: WireVec, index: egglog.i64Like): ...   # index is decremented each step

# union_vec_iter_rule = egglog.rule(union_vec(ws0, wv0, i), i >= 0).then(
#     egglog.subsume(union_vec(ws0, wv0, i)),
#     egglog.union(ws0[i]).with_(wv0[i]),
#     union_vec(ws0, wv0, i - 1)
# )

class build_dffs(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, ds: egglog.Vec[Wire], qs: egglog.Vec[Wire]): ...

build_dffs_iter_rule = egglog.rule(build_dffs(ws0, ws1), ws0.length() > ws1.length()).then(
    egglog.subsume(build_dffs(ws0, ws1)),
    build_dffs(ws0, ws1.push(Wire.from_dff(ws0[ws1.length()])))  # push a new dff q port
)

# NOTE: run once
arith_retiming_backward_start_rules = egglog.ruleset(
    egglog.rule(
        egglog.eq(wv0).to(WireVec.add(ws0, ws1)),
        all_to_dffs(wv0, ws2), ws2.length() >= ws0.length(),  # can be retimed
    ).then(
        build_dffs(ws0, egglog.Vec[Wire]()),
        build_dffs(ws1, egglog.Vec[Wire]())
    ),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.sub(ws0, ws1)),
        all_to_dffs(wv0, ws2), ws2.length() >= ws0.length(),  # can be retimed
    ).then(
        build_dffs(ws0, egglog.Vec[Wire]()),
        build_dffs(ws1, egglog.Vec[Wire]())
    ),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.sub(ws0, ws1)),
        all_to_dffs(wv0, ws2), ws2.length() >= ws0.length(),  # can be retimed
    ).then(
        build_dffs(ws0, egglog.Vec[Wire]()),
        build_dffs(ws1, egglog.Vec[Wire]())
    )
)

arith_retiming_backward_end_rules = egglog.ruleset(
    egglog.rule(
        egglog.eq(wv0).to(WireVec.add(ws0, ws1)),
        all_to_dffs(wv0, ws2), ws2.length() >= ws0.length(),
        build_dffs(ws0, ws3), ws3.length() >= ws0.length(), # input dffs built
        build_dffs(ws1, ws4), ws4.length() >= ws0.length()  # input dffs built
    ).then(union_dffs(wv0, WireVec.add(ws3, ws4), ws0.length() - 1)),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.sub(ws0, ws1)),
        all_to_dffs(wv0, ws2), ws2.length() >= ws0.length(),
        build_dffs(ws0, ws3), ws3.length() >= ws0.length(), # input dffs built
        build_dffs(ws1, ws4), ws4.length() >= ws0.length()  # input dffs built
    ).then(union_dffs(wv0, WireVec.sub(ws3, ws4), ws0.length() - 1)),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.mul(ws0, ws1)),
        all_to_dffs(wv0, ws2), ws2.length() >= ws0.length(),
        build_dffs(ws0, ws3), ws3.length() >= ws0.length(), # input dffs built
        build_dffs(ws1, ws4), ws4.length() >= ws0.length()  # input dffs built
    ).then(union_dffs(wv0, WireVec.mul(ws3, ws4), ws0.length() - 1))
)
