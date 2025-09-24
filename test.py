import emap
import json

TEST_NAME = "adder_simplified"
TOP_MODULE = "test_data_beta_runner/original_circuit"
MAX_ITER = 10

netlist = emap.NetlistDB(schema_file="emap/schema.sql", cnt=100000)
with open(f"eval/{TEST_NAME}.json") as f:
    netlist.build_from_json(json.load(f)["modules"][TOP_MODULE])

wdsu = emap.DisjointSetUnion()
netlist.rebuild(wdsu)

with open(f"netlist_before.json", "w") as f:
    json.dump(netlist.dump_tables(), f, indent=2)

for i in range(MAX_ITER):
    matches0 = emap.rewrites.ematch_not_idemp(netlist)
    matches1 = emap.rewrites.ematch_aby_idemp(netlist)
    matches2 = emap.rewrites.ematch_aby_comm(netlist)
    matches3 = emap.rewrites.ematch_aby_assoc_left(netlist)
    matches4 = emap.rewrites.ematch_andor_distrib(netlist)
    matches5 = emap.rewrites.ematch_orand_distrib(netlist)
    matches6 = emap.rewrites.ematch_absorp(netlist)
    # matches7 = emap.rewrites.ematch_th11(netlist)
    # matches8 = emap.rewrites.ematch_th13(netlist)
    # matches9 = emap.rewrites.ematch_th14(netlist)
    # matches10 = emap.rewrites.ematch_th15(netlist)
    # matches11 = emap.rewrites.ematch_th16(netlist)

    cnt = 0
    cnt += emap.rewrites.apply_not_idemp(matches0, wdsu)
    cnt += emap.rewrites.apply_aby_idemp(matches1, wdsu)
    cnt += emap.rewrites.apply_aby_comm(netlist, matches2)
    cnt += emap.rewrites.apply_aby_assoc_left(netlist, matches3)
    cnt += emap.rewrites.apply_andor_distrib(netlist, matches4)
    cnt += emap.rewrites.apply_orand_distrib(netlist, matches5)
    cnt += emap.rewrites.apply_absorp(matches6, wdsu)
    # cnt += emap.rewrites.apply_th11(netlist, matches7)
    # cnt += emap.rewrites.apply_th13(matches8, wdsu)
    # cnt += emap.rewrites.apply_th14(netlist, matches9)
    # cnt += emap.rewrites.apply_th15(matches10, wdsu)
    # cnt += emap.rewrites.apply_th16(netlist, matches11)

    if cnt > 0:
        print(f"Applied {cnt} rewrites")
        netlist.rebuild(wdsu)
        # assert len(wdsu.parents) == 0
        with open(f"netlist_iter_{i}.json", "w") as f:
            json.dump(netlist.dump_tables(), f, indent=2)
    else:
        print("No more rewrites can be applied. Stopping.")
        break

with open(f"netlist_after.json", "w") as f:
    json.dump(netlist.dump_tables(), f, indent=2)