import emap
import json

netlist = emap.Netlist()
with open("eval/out/add.json") as f:
    mod = json.load(f)["modules"]["add"]
netlist.build_from_json(mod)
netlist.display(graphviz=True)