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

SCHEMA_PATH = "emap/schema.sql"

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

TEST_NAME = "fft64"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["FFT"], clk="clock")

netlist.rebuild()

complex_mul_matches = emap.rewrites.ematch_complex_mul(netlist)
cnt = emap.rewrites.apply_complex_mul(netlist, complex_mul_matches)
print(f"Applied {cnt} rewrites")
netlist.rebuild()

cnt = 1
while cnt > 0:
    comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
    dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
    dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])

    cnt = emap.rewrites.apply_comm(netlist, comm_matches)
    cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
    cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_aby_cell_matches)
    if cnt > 0:
        print(f"Applied {cnt} rewrites")
    else:
        print("No rewrites applied, stopping")
    netlist.rebuild()

# techmapping
# basis: multiplication
emap.rewrites.create_tech_tables(netlist, dsp_rules)
emap.rewrites.techmap_dsp(netlist)
mod = emap.extracts.ilp.extract_techmap_with_limit(netlist, simple_cost_model, dsp_rules, {"dsp48e2": 16}, OutputFlag=False)

# with open(f"eval/out/{TEST_NAME}_extracted.json", "w") as f:
#     json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)