from .common import *


wirevec_length_rules = egglog.ruleset(
    egglog.rewrite(WireVec.add(ws0, ws1).length()).to(ws0.length()),
    egglog.rewrite(WireVec.sub(ws0, ws1).length()).to(ws0.length()),
    egglog.rewrite(WireVec.mul(ws0, ws1).length()).to(ws0.length())
)