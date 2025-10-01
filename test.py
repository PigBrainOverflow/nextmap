import emap
import json
import time

TEST_NAME = "adder"
TOP_MODULE = "eval/epfl/adder"
MAX_ITER = 4

start_time = time.time()

netlist = emap.NetlistDB(schema_file="emap/schema.sql", cnt=10000)
netlist.VERBOSE = True
with open(f"eval/epfl/{TEST_NAME}.json") as f:
    netlist.build_from_json(json.load(f)["modules"][TOP_MODULE])

wdsu = emap.DisjointSetUnion()
netlist.rebuild(wdsu)

for i in range(MAX_ITER):
    matches0 = emap.rewrites.ematch_not_idemp(netlist)
    matches1 = emap.rewrites.ematch_and_idemp(netlist)
    matches2 = emap.rewrites.ematch_and_assoc_left(netlist)
    matches3 = emap.rewrites.ematch_and_comm(netlist)
    matches4 = emap.rewrites.ematch_and_comp(netlist)

    cnt = 0
    cnt += emap.rewrites.apply_not_idemp(matches0, wdsu)
    cnt += emap.rewrites.apply_and_idemp(matches1, wdsu)
    cnt += emap.rewrites.apply_and_assoc_left(netlist, matches2)
    cnt += emap.rewrites.apply_and_comm(netlist, matches3)
    cnt += emap.rewrites.apply_and_comp(matches4, wdsu)

    if cnt > 0:
        print(f"Applied {cnt} rewrites")
        netlist.rebuild(wdsu)
    else:
        print("No more rewrites can be applied. Stopping.")
        break

# lut map
emap.rewrites.techmap_luts(netlist, k=6, cnt=100, rseed=42)

with open("debug.json", "w") as f:
    json.dump(netlist.dump_tables(), f, indent=2)

with open(f"eval/out/saturated_{TEST_NAME}.json", "w") as f:
    json.dump({"creator": "nextmap", "modules": {"top": netlist.write_json()}}, f, indent=2)