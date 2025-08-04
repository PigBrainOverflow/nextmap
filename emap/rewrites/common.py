import egglog
from ..core import Wire, WireVec


i, j = egglog.vars_("i j", egglog.i64)
w0, w1 = egglog.vars_("w0 w1", Wire)
wv0, wv1 = egglog.vars_("wv0 wv1", WireVec)
ws0, ws1, ws2, ws3 = egglog.vars_("ws0 ws1 ws2 ws3", egglog.Vec[Wire])