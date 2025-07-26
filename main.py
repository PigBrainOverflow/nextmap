# import gurobipy as grb


# model = grb.read("systolic.lp")

# model.computeIIS()
# model.write("systolic.ilp")

import json

with open("hello.json", "w") as f:
    json.dump({"hello": "world"}, f, indent=2)