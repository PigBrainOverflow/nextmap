import emap
import json

SCHEMA_PATH = "emap/schema.sql"

TEST_NAME = "sync_mem_1r1w"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["top"])
netlist.rebuild()

# cnt = 1
# while cnt > 0:
#     dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$mulu"])

#     cnt = emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
#     if cnt > 0:
#         print(f"Applied {cnt} rewrites")
#     else:
#         print("No rewrites applied, stopping")
#     netlist.rebuild()

with open(f"debug.json", "w") as f:
    json.dump(netlist.dump_tables(), f, indent=2)

# with open(f"eval/out/{TEST_NAME}_extracted.json", "w") as f:
#     json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)