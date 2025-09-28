from ..db import NetlistDB
from .utils import db_to_normalized, db_to_normalized_tech, normalized_to_json
from .solver_interface import create_solver, quicksum, GRB
from typing import Any, Callable
import importlib
import numpy as np
import scipy.sparse as sp
import os


def prune_cells(cells: list[dict[str, Any]]):
    """
    Modify cells in place.
    """
    try:
        emapcc = importlib.import_module("..emapcc.build.emapcc", package=__package__)
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
    except (ImportError, AttributeError) as e:
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
        emapcc = importlib.import_module("..emapcc.build.emapcc", package=__package__)
        print("C++ backend emapcc found")
        cnt = len(set().union(*bundles))
        new_bundles, groups = emapcc.group_wires(bundles)
        for bundle, new_bundle in zip(bundles, new_bundles):    # modify in place
            bundle.clear()
            bundle |= set(new_bundle)
        print(f"Grouped {cnt} wires into {len(groups)} groups")
        return groups
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

def add_wire_constrs(ilp_model, x, y, z, groups: list[set[int]], cells: list[dict[str, Any]], dffs: list[dict[str, Any]], all_source: set[int]):
    n_constrs, n_vars = len(groups), len(x) + len(y) + len(z)
    A = sp.lil_matrix((n_constrs, n_vars), dtype=int)
    rhs = np.zeros(n_constrs, dtype=int)
    sense = [">"] * n_constrs

    # add cells
    for i, cell in enumerate(cells):
        for gid in cell["all_outputs"]:
            if gid not in all_source:
                A[gid, len(x) + i] = 1  # y[i]

    # add dffs
    for i, dff in enumerate(dffs):
        for gid in dff["all_outputs"]:
            if gid not in all_source:
                A[gid, len(x) + len(y) + i] = 1 # z[i]

    for gid in range(len(groups)):
        if gid not in all_source:
            A[gid, gid] = -1

    ilp_model.addMConstr(A=A, x=None, sense=sense, b=rhs, name="wire_constraints")

def extract_no_techmap(db: NetlistDB, cost_model: Callable, solver_type: str = "auto", **solver_args) -> dict:
    """
    Return a module in Yosys JSON format.

    Args:
        db: NetlistDB instance
        cost_model: Cost function for cells
        solver_type: "gurobi", "cbc", or "auto" (default)
        **solver_args: Additional solver parameters
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
    ilp_model = create_solver(solver_type)
    for k, v in solver_args.items():
        ilp_model.setParam(k, v)
    x = ilp_model.addVars(len(groups), vtype=GRB.BINARY, name="x")  # choices of wires
    y = ilp_model.addVars(len(cells), vtype=GRB.BINARY, name="y")   # choices of cells
    z = ilp_model.addVars(len(dffs), vtype=GRB.BINARY, name="z")    # choices of dffs
    ilp_model.addConstrs((x[group] >= 1 for group in all_sink), "output_constraints")

    add_wire_constrs(ilp_model, x, y, z, groups, cells, dffs, all_source)

    for i, cell in enumerate(cells):
        for gid in cell["all_inputs"]:
            ilp_model.addConstr(x[gid] >= y[i], f"cell_{i}_input_{gid}_constraint") # if the cell is chosen, all its inputs must be chosen
    for i, dff in enumerate(dffs):
        for gid in dff["all_inputs"]:
            ilp_model.addConstr(x[gid] >= z[i], f"dff_{i}_input_{gid}_constraint")  # if the dff is chosen, all its inputs must be chosen

    # Set objective using our solver interface
    obj_expr = quicksum([y[i] * cells[i]["cost"] for i in range(len(cells))], solver=ilp_model)
    if dffs:
        obj_expr += quicksum([z[i] * dffs[i]["cost"] for i in range(len(dffs))], solver=ilp_model)
    ilp_model.setObjective(obj_expr, GRB.MINIMIZE)

    ilp_model.optimize()

    if ilp_model.status == GRB.INFEASIBLE:
        raise ValueError("ILP model is infeasible, no solution found.")
    if ilp_model.status == GRB.UNBOUNDED:
        raise ValueError("ILP model is unbounded, no solution found.")
    print(f"ILP model solved with objective value: {ilp_model.objVal}")

    # extract solution
    cells_selected = [cell for i, cell in enumerate(cells) if y[i].X > 0.5]
    dffs_selected = [dff for i, dff in enumerate(dffs) if z[i].X > 0.5]

    return normalized_to_json(db, {}, inputs, outputs, cells_selected, dffs_selected)


def extract_techmap_with_limit(db: NetlistDB, cost_model: Callable, tech_rules: dict[str, dict[str, Any]], tech_limits: dict[str, int], solver_type: str = "auto", **solver_args) -> dict:
    """
    Return a module in Yosys JSON format.

    Args:
        db: NetlistDB instance
        cost_model: Cost function for cells
        tech_rules: Technology mapping rules
        tech_limits: Limits for technology cells
        solver_type: "gurobi", "cbc", or "auto" (default)
        **solver_args: Additional solver parameters
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
    ilp_model = create_solver(solver_type)
    for k, v in solver_args.items():
        ilp_model.setParam(k, v)
    x = ilp_model.addVars(len(groups), vtype=GRB.BINARY, name="x")  # choices of wires
    y = ilp_model.addVars(len(cells), vtype=GRB.BINARY, name="y")   # choices of cells
    z = ilp_model.addVars(len(dffs), vtype=GRB.BINARY, name="z")    # choices of dffs
    ilp_model.addConstrs((x[group] >= 1 for group in all_sink), "output_constraints")

    add_wire_constrs(ilp_model, x, y, z, groups, cells, dffs, all_source)

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

        limit_expr = quicksum([cs[i] * y[i] for i in range(len(cells)) if cs[i] > 0], solver=ilp_model)
        ilp_model.addConstr(limit_expr <= limit, f"tech_limit_{tech_name}")

    # Set objective using our solver interface
    obj_expr = quicksum([y[i] * cells[i]["cost"] for i in range(len(cells))], solver=ilp_model)
    if dffs:
        obj_expr += quicksum([z[i] * dffs[i]["cost"] for i in range(len(dffs))], solver=ilp_model)
    ilp_model.setObjective(obj_expr, GRB.MINIMIZE)

    ilp_model.optimize()

    if ilp_model.status == GRB.INFEASIBLE:
        raise ValueError("ILP model is infeasible, no solution found.")
    if ilp_model.status == GRB.UNBOUNDED:
        raise ValueError("ILP model is unbounded, no solution found.")
    print(f"ILP model solved with objective value: {ilp_model.objVal}")

    # extract solution
    cells_selected = [cell for i, cell in enumerate(cells) if y[i].X > 0.5]
    dffs_selected = [dff for i, dff in enumerate(dffs) if z[i].X > 0.5]

    return normalized_to_json(db, tech_rules, inputs, outputs, cells_selected, dffs_selected)