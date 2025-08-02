import egglog
from ....core import WireVec
from ...misc import length_of


@egglog.function
def dsp48e2_unsigned_mul_0_stage_25_17_48_bit(a: WireVec, b: WireVec) -> WireVec: ...

i, j, k = egglog.vars_("i j k", egglog.i64)
wv0, wv1, wv2 = egglog.vars_("wv0 wv1 wv2", WireVec)

dsp_rules = egglog.ruleset(
    egglog.rule(
        egglog.eq(wv0).to(WireVec.mul(i, WireVec.zero_extended(i, wv1), WireVec.zero_extended(i, wv2))), i <= 48,
        length_of(wv1, j), j <= 25,
        length_of(wv2, k), k <= 17,
    ).then(egglog.union(dsp48e2_unsigned_mul_0_stage_25_17_48_bit(wv1, wv2)).with_(wv0))
)