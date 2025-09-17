from ..core import *


w0, w1, w2 = egglog.vars_("w0 w1 w2", Wire)

comm_rules = egglog.ruleset(
    egglog.rewrite(w0 & w1).to(w1 & w0),
    egglog.rewrite(w0 | w1).to(w1 | w0),
    egglog.rewrite(w0 ^ w1).to(w1 ^ w0)
)

assoc_rules = egglog.ruleset(
    egglog.birewrite((w0 & w1) & w2).to(w0 & (w1 & w2)),
    egglog.birewrite((w0 | w1) | w2).to(w0 | (w1 | w2)),
    egglog.birewrite((w0 ^ w1) ^ w2).to(w0 ^ (w1 ^ w2))
)

distrib_rules = egglog.ruleset(
    egglog.birewrite(w0 & (w1 | w2)).to((w0 & w1) | (w0 & w2)),
    egglog.birewrite(w0 | (w1 & w2)).to((w0 | w1) & (w0 | w2))
)

idemp_rules = egglog.ruleset(
    egglog.rewrite(w0 & w0).to(w0),
    egglog.rewrite(w0 | w0).to(w0),
    egglog.rewrite(w0 ^ w0).to(Wire.const("0")),
    egglog.rewrite(~~w0).to(w0)
)

demorgan_rules = egglog.ruleset(
    egglog.birewrite(~(w0 & w1)).to(~w0 | ~w1),
    egglog.birewrite(~(w0 | w1)).to(~w0 & ~w1)
)

mux_rules = egglog.ruleset(
    egglog.rewrite(Wire.mux(w0, w1, Wire.const("0"))).to(w0),
    egglog.rewrite(Wire.mux(w0, w1, Wire.const("1"))).to(w1),
    egglog.rewrite(Wire.mux(w0, w0, w1)).to(w0)
)