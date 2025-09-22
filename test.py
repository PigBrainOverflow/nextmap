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

import emap
import json
import time

SCHEMA_PATH = "emap/schema.sql"
TEST_NAME = "systolic_matmul_16x16_w32"

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

start = time.time()
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["top"])
netlist.rebuild()

matches = emap.rewrites.ematch_wide_muls(netlist)
cnt = emap.rewrites.apply_wide_muls_split(netlist, matches)
print(f"Applied {cnt} rewrites")
cnt = emap.rewrites.apply_wide_muls_split_v2(netlist, matches)
print(f"Applied {cnt} rewrites")
netlist.rebuild()
matches = emap.rewrites.ematch_wide_dff(netlist)
cnt = emap.rewrites.apply_wide_dff_split(netlist, matches)
print(f"Applied {cnt} rewrites")
netlist.rebuild()

cnt = 1
while cnt > 0:
    comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
    dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
    dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])

    cnt = 0
    cnt += emap.rewrites.apply_comm(netlist, comm_matches)
    cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
    cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_aby_cell_matches)

    if cnt > 0:
        print(f"Applied {cnt} rewrites")
    else:
        print("No rewrites applied, stopping")
    netlist.rebuild()

print(f"Saturation time: {time.time() - start:.2f} seconds")
start = time.time()

# techmapping
emap.rewrites.create_tech_tables(netlist, dsp_rules)
emap.rewrites.techmap_dsp(netlist)
print(f"Techmapping time: {time.time() - start:.2f} seconds")

start = time.time()
print("Starting ILP extraction")
mod = emap.extracts.ilp.extract_techmap_with_limit(netlist, simple_cost_model, dsp_rules, {"dsp48e2": 704})
print(f"ILP extraction time: {time.time() - start:.2f} seconds")
with open(f"eval/out/{TEST_NAME}_extracted.json", "w") as f:
    json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)