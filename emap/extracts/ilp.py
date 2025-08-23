from ..db import NetlistDB
from .utils import db_to_normalized, db_to_normalized_tech, normalized_to_json
from typing import Any, Callable
import importlib
import gurobipy as grb
# import numpy as np
# import scipy.sparse as sp


def prune_cells(cells: list[dict[str, Any]]):
    """
    Modify cells in place.
    """
    try:
        emapcc = importlib.import_module("..emapcc.build", package=__package__).emapcc
        print("C++ backend emapcc found")
        removed_indices = emapcc.prune_cells([(
            cell["cost"],
            sorted({w for ws in cell["inputs"].values() for w in ws}),
            sorted({w for ws in cell["outputs"].values() for w in ws})
        ) for cell in cells])
        wr = 0
        for rd in range(len(cells)):
            if rd not in removed_indices:
                cells[wr] = cells[rd]
                wr += 1
        cells = cells[:wr]  # truncate
        print(f"Removed {len(removed_indices)} dominated cells, {len(cells)} remain")
    except (ImportError, AttributeError):
        print("C++ backend emapcc not found")
        # fallback to Python implementation
        cell_inputs: list[set[int]] = [{w for ws in cell["inputs"].values() for w in ws} for cell in cells]
        cell_outputs: list[set[int]] = [{w for ws in cell["outputs"].values() for w in ws} for cell in cells]
        modified = True
        cnt = 0
        while modified:
            modified = False
            for i in range(len(cells)):
                for j in range(len(cells)):
                    if i != j and cells[i]["cost"] >= cells[j]["cost"] and cell_inputs[i] >= cell_inputs[j] and cell_outputs[i] <= cell_outputs[j]:
                        # cell i is dominated by cell j
                        cells.pop(i)
                        cell_inputs.pop(i)
                        cell_outputs.pop(i)
                        modified = True
                        cnt += 1
                        break
                if modified:
                    break
        print(f"Removed {cnt} dominated cells, {len(cells)} remain")

def group_wires(bundles: list[set[int]]) -> list[set[int]]:
    """
    Modify bundles in place.
    Return a list of groups of wires.
    """
    try:
        emapcc = importlib.import_module("..emapcc.build", package=__package__).emapcc
        print("C++ backend emapcc found")
        raise NotImplementedError("C++ backend for group_wires() not implemented yet")
    except (ImportError, AttributeError):
        print("C++ backend emapcc not found")
        # fallback to Python implementation
        groups: list[set[int]] = []
        new_bundles: list[set[int]] = [set() for _ in range(len(bundles))]
        wires = set().union(*bundles)
        for wire in wires:
            # find a bundle that contains this wire
            wire_group = None
            for i, bundle in enumerate(bundles):
                if wire in bundle:
                    wire_group = set(bundle)  # make a copy
                    break
            else:
                continue  # no bundle found for this wire, skip it
            # shrink the wire group
            found_in: list[int] = []
            for i, bundle in enumerate(bundles):
                if wire in bundle:
                    found_in.append(i)
                    wire_group &= bundle
                else:
                    wire_group -= bundle
            # update bundles
            for i in found_in:
                bundles[i] -= wire_group
                new_bundles[i].add(len(groups))
            groups.append(wire_group)
        for bundle, new_bundle in zip(bundles, new_bundles):    # modify in place
            bundle.clear()
            bundle |= new_bundle
        print(f"Grouped {len(wires)} wires into {len(groups)} groups")
        return groups

def extract_no_techmap(db: NetlistDB, cost_model: Callable, **grb_args) -> dict:
    """
    Return a module in Yosys JSON format.
    """
    inputs, outputs, cells, dffs = db_to_normalized(db, cost_model)

    # prune cells that are dominated by others
    prune_cells(cells)

    # group wires
    all_source = {-1, 0, 1} | {w for ws in inputs.values() for w in ws} # consts + inputs
    all_sink = {w for ws in outputs.values() for w in ws}
    bundles: list[set[int]] = [all_source, all_sink]
    for cell in cells:
        cell["all_inputs"] = {w for ws in cell["inputs"].values() for w in ws}
        cell["all_outputs"] = {w for ws in cell["outputs"].values() for w in ws}
        bundles.append(cell["all_inputs"])
        bundles.append(cell["all_outputs"])
    for dff in dffs:
        dff["all_inputs"] = {w for ws in dff["inputs"].values() for w in ws}
        dff["all_outputs"] = {w for ws in dff["outputs"].values() for w in ws}
        bundles.append(dff["all_inputs"])
        bundles.append(dff["all_outputs"])
    groups = group_wires(bundles)

    # build ILP
    ilp_model = grb.Model()
    for k, v in grb_args.items():
        ilp_model.setParam(k, v)
    x = ilp_model.addVars(len(groups), vtype=grb.GRB.BINARY, name="x")  # choices of wires
    y = ilp_model.addVars(len(cells), vtype=grb.GRB.BINARY, name="y")   # choices of cells
    z = ilp_model.addVars(len(dffs), vtype=grb.GRB.BINARY, name="z")    # choices of dffs
    ilp_model.addConstrs((x[group] >= 1 for group in all_sink), "output_constraints")
    ilp_model.addConstrs((
        grb.quicksum(y[i] for i in range(len(cells)) if gid in cells[i]["all_outputs"])
        + grb.quicksum(z[i] for i in range(len(dffs)) if gid in dffs[i]["all_outputs"])
        >= x[gid] for gid in range(len(groups)) if gid not in all_source),
        "wire_constraints"
    )
    for i, cell in enumerate(cells):
        for gid in cell["all_inputs"]:
            ilp_model.addConstr(x[gid] >= y[i], f"cell_{i}_input_{gid}_constraint") # if the cell is chosen, all its inputs must be chosen
    for i, dff in enumerate(dffs):
        for gid in dff["all_inputs"]:
            ilp_model.addConstr(x[gid] >= z[i], f"dff_{i}_input_{gid}_constraint")  # if the dff is chosen, all its inputs must be chosen
    ilp_model.setObjective(
        grb.quicksum(y[i] * cells[i]["cost"] for i in range(len(cells)))
        + grb.quicksum(z[i] * dffs[i]["cost"] for i in range(len(dffs))),
        grb.GRB.MINIMIZE
    )   # minimize the total cost

    # print(all_source, all_sink)
    # for cell in cells:
    #     print(cell["all_inputs"], cell["all_outputs"])
    # for dff in dffs:
    #     print(dff["all_inputs"], dff["all_outputs"])
    # ilp_model.write("egraph_extraction.lp")
    ilp_model.optimize()

    if ilp_model.status == grb.GRB.INFEASIBLE:
        raise ValueError("ILP model is infeasible, no solution found.")
    if ilp_model.status == grb.GRB.UNBOUNDED:
        raise ValueError("ILP model is unbounded, no solution found.")
    print(f"ILP model solved with objective value: {ilp_model.objVal}")

    # extract solution
    cells_selected = [cell for i, cell in enumerate(cells) if y[i].X > 0.5]
    dffs_selected = [dff for i, dff in enumerate(dffs) if z[i].X > 0.5]

    return normalized_to_json(db, inputs, outputs, cells_selected, dffs_selected)


def extract_techmap_with_limit(db: NetlistDB, cost_model: Callable, tech_rules: dict[str, dict[str, Any]], tech_limits: dict[str, int], **grb_args) -> dict:
    """
    Return a module in Yosys JSON format.
    """
    inputs, outputs, cells, dffs = db_to_normalized(db, cost_model)
    cells += db_to_normalized_tech(db, cost_model, tech_rules)

    # prune cells that are dominated by others
    prune_cells(cells)

    # group wires
    all_source = {-1, 0, 1} | {w for ws in inputs.values() for w in ws} # consts + inputs
    all_sink = {w for ws in outputs.values() for w in ws}
    bundles: list[set[int]] = [all_source, all_sink]
    for cell in cells:
        cell["all_inputs"] = {w for ws in cell["inputs"].values() for w in ws}
        cell["all_outputs"] = {w for ws in cell["outputs"].values() for w in ws}
        bundles.append(cell["all_inputs"])
        bundles.append(cell["all_outputs"])
    for dff in dffs:
        dff["all_inputs"] = {w for ws in dff["inputs"].values() for w in ws}
        dff["all_outputs"] = {w for ws in dff["outputs"].values() for w in ws}
        bundles.append(dff["all_inputs"])
        bundles.append(dff["all_outputs"])
    groups = group_wires(bundles)

    # build ILP
    ilp_model = grb.Model()
    for k, v in grb_args.items():
        ilp_model.setParam(k, v)
    x = ilp_model.addVars(len(groups), vtype=grb.GRB.BINARY, name="x")  # choices of wires
    y = ilp_model.addVars(len(cells), vtype=grb.GRB.BINARY, name="y")   # choices of cells
    z = ilp_model.addVars(len(dffs), vtype=grb.GRB.BINARY, name="z")    # choices of dffs
    ilp_model.addConstrs((x[group] >= 1 for group in all_sink), "output_constraints")
    ilp_model.addConstrs((
        grb.quicksum(y[i] for i in range(len(cells)) if gid in cells[i]["all_outputs"])
        + grb.quicksum(z[i] for i in range(len(dffs)) if gid in dffs[i]["all_outputs"])
        >= x[gid] for gid in range(len(groups)) if gid not in all_source),
        "wire_constraints"
    )
    for i, cell in enumerate(cells):
        for gid in cell["all_inputs"]:
            ilp_model.addConstr(x[gid] >= y[i], f"cell_{i}_input_{gid}_constraint") # if the cell is chosen, all its inputs must be chosen
    for i, dff in enumerate(dffs):
        for gid in dff["all_inputs"]:
            ilp_model.addConstr(x[gid] >= z[i], f"dff_{i}_input_{gid}_constraint")  # if the dff is chosen, all its inputs must be chosen
    # tech cell usage limits
    for tech_name, limit in tech_limits.items():
        cs: list[int] = [0] * len(cells)    # coefficients of each cell
        for i, cell in enumerate(cells):
            type_ = cell["type"]
            if not type_.startswith("$"):
                cs[i] = tech_rules[type_]["requirements"].get(tech_name, 0)
        ilp_model.addConstr(
            grb.quicksum(cs[i] * y[i] for i in range(len(cells))) <= limit,
            f"tech_limit_{tech_name}"
        )

    ilp_model.setObjective(
        grb.quicksum(y[i] * cells[i]["cost"] for i in range(len(cells)))
        + grb.quicksum(z[i] * dffs[i]["cost"] for i in range(len(dffs))),
        grb.GRB.MINIMIZE
    )   # minimize the total cost

    ilp_model.optimize()

    if ilp_model.status == grb.GRB.INFEASIBLE:
        raise ValueError("ILP model is infeasible, no solution found.")
    if ilp_model.status == grb.GRB.UNBOUNDED:
        raise ValueError("ILP model is unbounded, no solution found.")
    print(f"ILP model solved with objective value: {ilp_model.objVal}")

    # extract solution
    cells_selected = [cell for i, cell in enumerate(cells) if y[i].X > 0.5]
    dffs_selected = [dff for i, dff in enumerate(dffs) if z[i].X > 0.5]

    return normalized_to_json(db, tech_rules, inputs, outputs, cells_selected, dffs_selected)