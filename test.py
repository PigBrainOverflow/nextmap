# prepare
import emap
import json

# for simplicity, the following examples all use this simple cost model
def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    elif type_.startswith("$"): # other types
        return len(ports[0]) * 1.0
    return 0.0  # blackboxes or tech cells

TEST_NAME = "redundant_adders"
SCHEMA_PATH = "emap/schema.sql"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["top"])

netlist.rebuild()
with open(f"{TEST_NAME}_initial.json", "w") as f:
    json.dump(netlist.dump_tables(), f, indent=2)

# cnt = 1
# while cnt > 0:
#     unsigned_add_matches = emap.rewrites.select_aby_cell_by_type(netlist, ["$addu"])
#     cnt = emap.rewrites.apply_unsigned_add_bitblast(netlist, ((a, b, y) for _, a, b, y in unsigned_add_matches))
#     if cnt > 0:
#         print(f"Applied {cnt} rewrites")
#     else:
#         print("No rewrites 
unsigned_add_matches = emap.rewrites.select_aby_cell_by_type(netlist, ["$addu"])
cnt = emap.rewrites.apply_unsigned_add_bitblast(netlist, ((a, b, y) for _, a, b, y in unsigned_add_matches))
netlist.rebuild()
unsigned_add_matches = emap.rewrites.select_aby_cell_by_type(netlist, ["$addu"])
cnt = emap.rewrites.apply_unsigned_add_bitblast(netlist, ((a, b, y) for _, a, b, y in unsigned_add_matches))
netlist.rebuild()
with open(f"{TEST_NAME}_after_bitblast.json", "w") as f:
    json.dump([netlist.dump_wirevecs(), netlist.dump_tables()], f, indent=2)


mod = emap.extracts.ilp.extract_no_techmap(netlist, simple_cost_model, OutputFlag=False)
with open(f"{TEST_NAME}_extracted.json", "w") as f:
    json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)