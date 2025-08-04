from .common import *


width_of_rules = egglog.ruleset(
    egglog.rule(egglog.eq(wv0).to(WireVec.add(ws0, ws1))).then(width_of(WireVec.add(ws0, ws1), ws0.length())),
    egglog.rule(egglog.eq(wv0).to(WireVec.sub(ws0, ws1))).then(width_of(WireVec.sub(ws0, ws1), ws0.length())),
    egglog.rule(egglog.eq(wv0).to(WireVec.mul(ws0, ws1))).then(width_of(WireVec.mul(ws0, ws1), ws0.length()))
)