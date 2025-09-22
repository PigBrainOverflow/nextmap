import matplotlib.pyplot as plt

# x = [704, 768, 832, 960, 1024, 1088]
# y1 = [9434, 9629, 6883, 4096, 4096, 4096]
# y2 = [29408, 24960, 20512, 11616, 7168, 7168]

# plt.figure(figsize=(3.5, 2.5), dpi=300)  # small, high-res for paper
# plt.plot(x, y1, marker='o', label='Nextmap')
# plt.plot(x, y2, marker='s', label='Proprietary')

# plt.xlabel("DSP Limit")
# plt.ylabel("CARRY4 Usage")
# plt.legend(frameon=False)
# plt.grid(True, linestyle="--", alpha=0.4)

# plt.tight_layout()
# plt.savefig("carry4.pdf")   # vector format for paper

x = [704, 768, 832, 960, 1024, 1088]
y1 = [137411, 57488, 95819, 133988, 60928, 60928]
y2 = [155623, 130260, 104837, 53946, 28416, 28416]

plt.figure(figsize=(3.5, 2.5), dpi=300)  # small, high-res for paper
plt.plot(x, y1, marker='o', label='Nextmap')
plt.plot(x, y2, marker='s', label='Proprietary')

plt.xlabel("DSP Limit")
plt.ylabel("LUT Usage")
plt.legend(frameon=False)
plt.grid(True, linestyle="--", alpha=0.4)

plt.tight_layout()
plt.savefig("lut.pdf")   # vector format for paper

# import gurobipy as grb

# # Create model
# m = grb.Model("simple_lp")

# # Add variables (nonnegative by default)
# x = m.addVars(4, ub=1, name="x")
# y = m.addVars(3, ub=1, name="y")

# # Set objective
# m.setObjective(grb.quicksum(x), grb.GRB.MINIMIZE)

# # Add constraints
# m.addConstr(y[0] >= 1)

# m.addConstr(y[0] <= x[0] + x[1])
# m.addConstr(y[1] <= x[2])
# m.addConstr(y[2] <= x[3])

# m.addConstr(x[0] <= y[1])
# m.addConstr(x[0] <= y[2])
# m.addConstr(x[1] <= y[1])
# m.addConstr(x[1] <= y[2])

# # m.addConstr(x[2] + x[3] >= 1)


# # Optimize
# m.optimize()

# # Print results
# if m.status == grb.GRB.OPTIMAL:
#     print(f"Objective value = {m.objVal}")
#     for v in m.getVars():
#         print(f"{v.varName} = {v.x}")
