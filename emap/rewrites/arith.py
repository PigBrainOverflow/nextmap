from ..core import *


wv0, wv1, wv2 = egglog.vars_("wv0 wv1 wv2", WireVec)

comm_rules = egglog.ruleset(
    egglog.rewrite(wv0 + wv1).to(wv1 + wv0),
    egglog.rewrite(wv0 * wv1).to(wv1 * wv0)
)

assoc_rules = egglog.ruleset(
    egglog.birewrite((wv0 + wv1) + wv2).to(wv0 + (wv1 + wv2)),
    egglog.birewrite((wv0 * wv1) * wv2).to(wv0 * (wv1 * wv2))
)

distrib_rules = egglog.ruleset(
    egglog.birewrite(wv0 * (wv1 + wv2)).to((wv0 * wv1) + (wv0 * wv2)),
    egglog.birewrite(wv0 * (wv1 - wv2)).to((wv0 * wv1) - (wv0 * wv2))
)
