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

SCHEMA_PATH = "emap/schema.sql"
TEST_NAME = "nerv"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["nerv"], clk="clock")

netlist.rebuild()
