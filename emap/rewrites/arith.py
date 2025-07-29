import egglog
from ..core import Wire, WireVec


i, j = egglog.vars_("i j", egglog.i64)
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)

arith_rules = egglog.ruleset(
    egglog.rewrite(WireVec.add(i, wv0, wv1)).to(WireVec.add(i, wv1, wv0)),
    egglog.rewrite(WireVec.mul(i, wv0, wv1)).to(WireVec.mul(i, wv1, wv0))
)