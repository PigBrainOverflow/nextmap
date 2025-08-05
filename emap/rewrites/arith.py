from .common import *


# TODO: add more rules, e.g., https://arxiv.org/html/2406.12421v1
arith_comm_rules = egglog.ruleset(
    egglog.rewrite(WireVec.add(ws0, ws1)).to(WireVec.add(ws1, ws0)),
    egglog.rewrite(WireVec.mul(ws0, ws1)).to(WireVec.mul(ws1, ws0))
)


##################
# Zero Extension #
##################
class zero_extended(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, ws: egglog.Vec[Wire], width: egglog.i64Like): ...    # width is the actual width of ws (before zero extension)

zero_extended_iter_rule = egglog.rule(
    zero_extended(ws0, i), i > 0,
    egglog.eq(ws0[i - 1]).to(Wire.from_const(0))
).then(
    egglog.subsume(zero_extended(ws0, i)),
    zero_extended(ws0, i - 1)
)

zero_extended_base_rules = egglog.ruleset(
    # NOTE: we only consider add, sub, mul here
    egglog.rule(WireVec.add(ws0, ws1)).then(
        zero_extended(ws0, ws0.length()),
        zero_extended(ws1, ws1.length())
    ),
    egglog.rule(WireVec.sub(ws0, ws1)).then(
        zero_extended(ws0, ws0.length()),
        zero_extended(ws1, ws1.length())
    ),
    egglog.rule(WireVec.mul(ws0, ws1)).then(
        zero_extended(ws0, ws0.length()),
        zero_extended(ws1, ws1.length())
    )
)


##################
# Sign Extension #
##################
class sign_extended(egglog.Expr):
    @egglog.method(unextractable=True)
    def __init__(self, ws: egglog.Vec[Wire], width: egglog.i64Like): ...    # width is the actual width of ws (before sign extension)

sign_extended_iter_rule = egglog.rule(
    sign_extended(ws0, i), i > 1,
    egglog.eq(ws0[i - 1]).to(ws0[i - 2])
).then(
    egglog.subsume(sign_extended(ws0, i)),
    sign_extended(ws0, i - 1)
)

sign_extended_base_rules = egglog.ruleset(
    # NOTE: we only consider add, sub, mul here
    egglog.rule(WireVec.add(ws0, ws1)).then(
        sign_extended(ws0, ws0.length()),
        sign_extended(ws1, ws1.length())
    ),
    egglog.rule(WireVec.sub(ws0, ws1)).then(
        sign_extended(ws0, ws0.length()),
        sign_extended(ws1, ws1.length())
    ),
    egglog.rule(WireVec.mul(ws0, ws1)).then(
        sign_extended(ws0, ws0.length()),
        sign_extended(ws1, ws1.length())
    )
)


##################
# Unsigned Arith #
##################
class unsigned(egglog.Expr):
    def __init__(self, wv: WireVec, out_width: egglog.i64Like, a_width: egglog.i64Like, b_width: egglog.i64Like): ...

arith_unsigned_rules = egglog.ruleset(
    egglog.rule(
        egglog.eq(wv0).to(WireVec.add(ws0, ws1)),
        zero_extended(ws0, i),
        zero_extended(ws1, j)
    ).then(unsigned(wv0, ws0.length(), i, j)),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.sub(ws0, ws1)),
        zero_extended(ws0, i),
        zero_extended(ws1, j)
    ).then(unsigned(wv0, ws0.length(), i, j)),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.mul(ws0, ws1)),
        zero_extended(ws0, i),
        zero_extended(ws1, j)
    ).then(unsigned(wv0, ws0.length(), i, j))
)


################
# Signed Arith #
################
class signed(egglog.Expr):
    def __init__(self, wv: WireVec, out_width: egglog.i64Like, a_width: egglog.i64Like, b_width: egglog.i64Like): ...

arith_signed_rules = egglog.ruleset(
    egglog.rule(
        egglog.eq(wv0).to(WireVec.add(ws0, ws1)),
        sign_extended(ws0, i),
        sign_extended(ws1, j)
    ).then(signed(wv0, ws0.length(), i, j)),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.sub(ws0, ws1)),
        sign_extended(ws0, i),
        sign_extended(ws1, j)
    ).then(signed(wv0, ws0.length(), i, j)),
    egglog.rule(
        egglog.eq(wv0).to(WireVec.mul(ws0, ws1)),
        sign_extended(ws0, i),
        sign_extended(ws1, j)
    ).then(signed(wv0, ws0.length(), i, j))
)