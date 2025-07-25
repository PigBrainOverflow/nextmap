# import gurobipy as grb


# model = grb.read("systolic.lp")

# model.computeIIS()
# model.write("systolic.ilp")

import json

with open("group.json", "r") as f:
    groups = json.load(f)

print(groups[7337])