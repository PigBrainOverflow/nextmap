import egglog
from ..core import Wire


w0, w1 = egglog.vars_("w0 w1", Wire)

logic_rules = egglog.ruleset(
    egglog.rewrite(w0 & w1).to(w1 & w0),
    egglog.rewrite(w0 | w1).to(w1 | w0),
    egglog.rewrite(w0 ^ w1).to(w1 ^ w0),
    egglog.rewrite(~~w0).to(w0)
)