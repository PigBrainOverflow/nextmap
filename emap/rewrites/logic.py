from .common import *


# TODO: add more rules, e.g., https://arxiv.org/html/2406.12421v1
logic_rules = egglog.ruleset(
    egglog.rewrite(w0 & w1).to(w1 & w0),
    egglog.rewrite(w0 | w1).to(w1 | w0),
    egglog.rewrite(w0 ^ w1).to(w1 ^ w0),
    egglog.rewrite(~~w0).to(w0)
)