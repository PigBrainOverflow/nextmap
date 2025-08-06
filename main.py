from typing import Callable
import os
import subprocess
import json
from emap import *

def import_design(design_path: str, top: str = "top") -> NetlistDB:
    db = NetlistDB("emap/schema.sql", ":memory:", cnt=1000000)
    with open(design_path, "r") as f:
        mod = json.load(f)
    db.build_from_json(mod["modules"][top])
    return db


dsp_rule_path = "./tests/rulesets/xilinx-xcup/dsp.json"
with open(dsp_rule_path, "r") as f:
    dsp_rules = json.load(f)
# no need to synthesize
def simple_cost_model(x: tuple) -> float:
    if x[0] in {"$muls", "$mulu"}:
        return NetlistDB.width_of(x[1]) * NetlistDB.width_of(x[2]) * 1.0
    elif x[0] == "$dff":
        return NetlistDB.width_of(x[1]) * 0.5
    else:
        return NetlistDB.width_of(x[1]) + NetlistDB.width_of(x[2]) * 1.0

print("Testing Systolic...")
db = import_design("./tests/designs/systolic/systolic.json", top="systolic")
rewrites.create_dsp_tables(db, dsp_rules)
# rewrite
# while rewrites.rewrite_dff_backward_aby_cell(db, ["$adds", "$addu", "$subs", "$subu", "$muls", "$mulu"]) > 0:
#     pass
rewrites.rewrite_comm(db, ["$adds", "$addu", "$subs", "$subu", "$muls", "$mulu"])
db.rebuild()
# for rule in dsp_rules:
#     print(f"Applied {rule['name']} {rewrites.rewrite_dsp(db, rule)} times.")
with open("out.json", "w") as f:
    json.dump(db.dump_tables(), f, indent=2)
# extract
# design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=2048, cost_model=simple_cost_model, verbose=True)  # try insufficient count, try different cost model
# # design = extracts.ilp.extract_dsps_by_cost(db, "dsp48e2", cost_model=simple_cost_model)
# os.makedirs("./tests/out/systolic", exist_ok=True)
# with open("./tests/out/systolic/systolic.json", "w") as f:
#     json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)