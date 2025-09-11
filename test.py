import emap
import json

SCHEMA_PATH = "emap/schema.sql"
TEST_NAME = "signed_addmulsub_2_stage_rst"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["top"])

netlist.rebuild()

# cnt = 1
# while cnt > 0:
#     dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls", "$subs"])
#     comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])

#     cnt = emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_aby_cell_matches)
#     cnt += emap.rewrites.apply_comm(netlist, comm_matches)
#     if cnt > 0:
#         print(f"Applied {cnt} rewrites")
#     else:
#         print("No rewrites applied, stopping")
#     netlist.rebuild()

# techmapping
# basis: multiplication
cur = netlist.execute("""
    SELECT a, b, y FROM aby_cells
    WHERE type = '$muls' AND width_of(a) <= 27 AND width_of(b) <= 18 AND width_of(y) <= 48
""")
matches = []
for a, b, y in cur:
    matches.append(emap.rewrites.match_dsp(netlist, a, b, y))
print(json.dumps(matches, indent=2))
print(netlist.dump_tables())