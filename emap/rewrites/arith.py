from .common import *


# TODO: add more rules, e.g., https://arxiv.org/html/2406.12421v1
arith_comm_rules = egglog.ruleset(
    egglog.rewrite(WireVec.add(ws0, ws1)).to(WireVec.add(ws1, ws0)),
    egglog.rewrite(WireVec.mul(ws0, ws1)).to(WireVec.mul(ws1, ws0))
)