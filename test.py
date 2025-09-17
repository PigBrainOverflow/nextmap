import emap
import json
import time
netlist = emap.Netlist()
with open("eval/out/alu_w32.json") as f:
    mod = json.load(f)["modules"]["alu"]

start = time.time()
netlist.build_from_json(mod)
print(f"Build time: {time.time() - start:.2f}s")
start = time.time()
report = netlist.run((
    emap.rewrites.logic.comm_rules + emap.rewrites.logic.assoc_rules + emap.rewrites.logic.demorgan_rules +
    emap.rewrites.logic.distrib_rules + emap.rewrites.logic.idemp_rules + emap.rewrites.logic.mux_rules +
    emap.rewrites.arith.comm_rules + emap.rewrites.arith.assoc_rules + emap.rewrites.arith.distrib_rules +
    emap.rewrites.basic.wirevec_canonicalize_rules
) * 4)
print(f"Rewrite time: {time.time() - start:.2f}s")

# for name, cnt in report.num_matches_per_rule.items():
#     print(f"{name}: {cnt}")
# netlist.display(graphviz=True)