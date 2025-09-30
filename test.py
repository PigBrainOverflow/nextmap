import emap
import json
import time

SCHEMA_PATH = "emap/schema.sql"

dsp_rules = {
    "dsp_generic": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["inputs"],
        "outputs": ["outputs"]
    }
}

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    elif type_.startswith("dsp"):   # tech cells
        return 0.0
    return len(ports[0]) * 1.0  # other types

start = time.time()
TEST_NAME = "ad_bd_cd_e"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["top"])
netlist.rebuild()

# rewrite
cnt = 1
for _ in range(10):
    comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
    distr_matches = emap.rewrites.ematch_distr_fold(netlist)
    assoc_left_matches = emap.rewrites.ematch_assoc_to_left(netlist, ["$adds", "$muls"])
    # assoc_right_matches = emap.rewrites.ematch_assoc_to_right(netlist, ["$adds", "$muls"])

    cnt =  0
    cnt += emap.rewrites.apply_comm(netlist, comm_matches)
    cnt += emap.rewrites.apply_distr_fold(netlist, distr_matches)
    cnt += emap.rewrites.apply_assoc_to_left(netlist, assoc_left_matches)
    # cnt += emap.rewrites.apply_assoc_to_right(netlist, assoc_right_matches)
    if cnt > 0:
        print(f"Applied {cnt} rewrites")
    else:
        print("No rewrites applied, stopping")
        break
    netlist.rebuild()

# techmap
emap.rewrites.create_tech_tables(netlist, dsp_rules)
emap.rewrites.techmap_dsp(netlist)

with open("debug.json", "w") as f:
    json.dump(netlist.dump_tables(), f, indent=2)

# extract
mod = emap.extracts.ilp.extract_techmap_with_limit(netlist, simple_cost_model, dsp_rules, {"dsp48e2": 2}, OutputFlag=False)

with open(f"eval/out/{TEST_NAME}_extracted.json", "w") as f:
    json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)