import egglog
from ..core import Wire, WireVec


i = egglog.var("i", egglog.i64)
w0 = egglog.var("w0", Wire)
wv0, wv1, wv2 = egglog.vars_("wv0 wv1 wv2", WireVec)
ws0, ws1, ws2, ws3 = egglog.vars_("ws0 ws1 ws2 ws3", egglog.Vec[Wire])

wirevec_primitive_rules = egglog.ruleset(
    egglog.rewrite(WireVec(ws0).length()).to(ws0.length()),
    egglog.rewrite(WireVec.zero_extended(i, wv0).length()).to(i),
    egglog.rewrite(WireVec.sign_extended(i, wv0).length()).to(i),
    egglog.rewrite(WireVec.add(i, wv0, wv1).length()).to(i),
    egglog.rewrite(WireVec.sub(i, wv0, wv1).length()).to(i),
    egglog.rewrite(WireVec.mul(i, wv0, wv1).length()).to(i),

    egglog.rewrite(WireVec(ws0)[i]).to(ws0[i]),

    egglog.rewrite(WireVec(ws0).push(w0)).to(WireVec(ws0.push(w0))),
    egglog.rewrite(WireVec(ws0).pop()).to(WireVec(ws0.pop()))
)