from ..db import NetlistDB
from .utils import Cell, DFF, db_to_normalized, db_to_json
from typing import Iterable, Callable
import gurobipy as grb
import time
import json


def _group_wires(bundles: list[set]) -> dict[str, set]:
    """
    Return a dictionary mapping each wire group to its corresponding set of wires.
    Modifies the input list of wires in place.
    For example, if bundles = [{1,2}, {1,2,3}, {3,4}], the output will be: [{1,2}, {3}, {4}].
    In most cases, this can significantly reduce the number of wires
    """
    groups = {}
    cnt = 0
    wires = set().union(*bundles)

    for wire in wires:
        # first, find a bundle that contains this wire
        wire_group = None
        for bundle in bundles:
            if wire in bundle:
                wire_group = {w for w in bundle if not isinstance(w, str) or not w.startswith("group")}
                break
        else:
            continue  # no bundle found for this wire, skip it
        # then, shrink the wire group
        for bundle in bundles:
            b = {w for w in bundle if not isinstance(w, str) or not w.startswith("group")}
            wire_group = b & wire_group if wire in b else wire_group - b
        # update bundles
        groups[f"group{cnt}"] = wire_group
        for bundle in bundles:
            if wire_group <= bundle:
                bundle -= wire_group
                bundle.add(f"group{cnt}")
        cnt += 1
        # print(f"Group {cnt} created for wires: {wire_group}")

    print(f"Grouped {len(wires)} wires into {len(groups)} groups.")
    return groups

def _group_wires_fast(bundles: list[set]) -> dict[str, set]:
    """
    A faster version of _group_wires() in C++.
    """
    phase_time = time.time()
    from ..cpp.build import emapcc
    # new_bundles, groups = emapcc.group_wires([{-1 if w == "x" else int(w) for w in bundle} for bundle in bundles])
    cnt = len(set().union(*bundles))
    new_bundles, groups = emapcc.group_wires_v2([{-1 if w == "x" else int(w) for w in bundle} for bundle in bundles])   # faster when set size and element frequency are bounded
    for i, bundle in enumerate(bundles):
        bundle.clear()
        bundle.update(f"group{gid}" for gid in new_bundles[i])
    print(f"_group_wires_fast() finished in {time.time() - phase_time:.2f} seconds, grouped {cnt} wires into {len(groups)} groups.")
    with open("group.json", "w") as f:
        json.dump(groups, f, indent=2)
    return {f"group{gid}": {int(w) for w in wires} for gid, wires in enumerate(groups)}

def _prune_cells(cells: list[Cell]):
    """
    Prune the cells that are dominated by other cells.
    """
    modified = True
    while modified:
        # print(f"Pruning cells, current count: {len(cells)}")
        modified = False
        for i in range(len(cells)):
            for j in range(len(cells)):
                if i != j and cells[i].cost >= cells[j].cost and cells[i].inputs >= cells[j].inputs and cells[i].outputs <= cells[j].outputs:
                    # cell i is dominated by cell j
                    cells.pop(i)
                    modified = True
                    break
            if modified:
                break

def _prune_cells_fast(cells: list[Cell]):
    """
    A faster version of _prune_cells() in C++.
    """
    phase_time = time.time()
    from ..cpp.build import emapcc
    removed_indices = emapcc.prune_cells([(
        cell.cost,
        sorted(-1 if w == "x" else int(w) for w in cell.inputs),
        sorted(-1 if w == "x" else int(w) for w in cell.outputs)
    ) for cell in cells])
    write = 0
    for read in range(len(cells)):
        if read not in removed_indices:
            cells[write] = cells[read]
            write += 1
    cells[:] = cells[:write]  # truncate the list to the new length
    print(f"_prune_cells_fast() finished in {time.time() - phase_time:.2f} seconds, removed {len(removed_indices)} cells, remaining {len(cells)} cells.")

def extract_dsps_by_cost(db: NetlistDB, name: str, cost_model: Callable) -> dict:
    cells, dffs = db_to_normalized(db, cost_model)

    # it's also possible to let users define the cost model for DSPs
    # for simplicity, we only consider the DSPs that are already fixed
    dsp_tables = db.tables_startswith(name)
    for dsp_table in dsp_tables:
        cur = db.execute(f"SELECT rowid, * FROM {dsp_table} WHERE value = 0")
        cells.update(Cell(table=dsp_table, rowid=row[0], inputs=set(",".join(row[2:-1]).split(",")), outputs=set(row[-1].split(",")), cost=0) for row in cur)

    cells, dffs = list(cells), list(dffs)
    input, output = set(), set()
    cur.execute("SELECT wire FROM ports WHERE direction = 'input'")
    for (wire,) in cur.fetchall():
        input.update(wire.split(","))
    cur.execute("SELECT wire FROM ports WHERE direction = 'output'")
    for (wire,) in cur.fetchall():
        output.update(wire.split(","))
    bundles = [input, output]
    bundles += [cell.inputs for cell in cells]
    bundles += [cell.outputs for cell in cells]
    bundles += [dff.d for dff in dffs]
    bundles += [dff.clk for dff in dffs]
    bundles += [dff.q for dff in dffs]
    # groups = list(_group_wires(bundles))    # this also modifies the input bundles into groups
    _prune_cells(cells)
    groups = list(_group_wires_fast(bundles))   # this also modifies the input bundles into groups

    # call gurobi to solve it
    ilp_model = grb.Model("egraph_extraction")
    ilp_model.setParam("OutputFlag", 0)
    x = ilp_model.addVars(len(groups), vtype=grb.GRB.BINARY, name="x") # choices of wires
    y = ilp_model.addVars(len(cells), vtype=grb.GRB.BINARY, name="y") # choices of cells
    z = ilp_model.addVars(len(dffs), vtype=grb.GRB.BINARY, name="z") # choices of dffs

    def gname_to_index(name: str) -> int:
        return int(name[5:])

    # output constraints
    for group in output:
        ilp_model.addConstr(x[gname_to_index(group)] >= 1, f"output_{group}_constraint")

    # wire constraints
    for group in groups:
        if group not in input:  # if the wire is not an input, it can be chosen or not
            # if the wire is chosen, at least one of the cells or dffs must be chosen
            ilp_model.addConstr(grb.quicksum(y[i] for i in range(len(cells)) if group in cells[i].outputs) + grb.quicksum(z[i] for i in range(len(dffs)) if group in dffs[i].q) >= x[gname_to_index(group)], f"wire_{group}_constraint")

    # cell constraints
    for i, cell in enumerate(cells):
        for group in cell.inputs:
            ilp_model.addConstr(x[gname_to_index(group)] >= y[i], f"cell_{i}_input_{group}_constraint")    # if the cell is chosen, all its inputs must be chosen

    # dff constraints
    for i, dff in enumerate(dffs):
        for group in dff.d:
            ilp_model.addConstr(x[gname_to_index(group)] >= z[i], f"dff_{i}_input_{group}_constraint")  # if the dff is chosen, all its inputs must be chosen
        for group in dff.clk:
            ilp_model.addConstr(x[gname_to_index(group)] >= z[i], f"dff_{i}_clk_{group}_constraint")    # if the dff is chosen, all its clocks must be chosen

    ilp_model.setObjective(
        grb.quicksum(y[i] * cells[i].cost for i in range(len(cells))) +
        grb.quicksum(z[i] * dffs[i].cost for i in range(len(dffs))),
        grb.GRB.MINIMIZE
    )   # minimize the total cost

    ilp_model.write("egraph_extraction.lp")
    ilp_model.optimize()

    if ilp_model.status != grb.GRB.OPTIMAL:
        raise ValueError("ILP model could not find an optimal solution.")
    if ilp_model.status == grb.GRB.INFEASIBLE:
        raise ValueError("ILP model is infeasible, no solution found.")
    if ilp_model.status == grb.GRB.UNBOUNDED:
        raise ValueError("ILP model is unbounded, no solution found.")
    print(f"ILP model solved with objective value: {ilp_model.objVal}")

    # extract the solution
    res: list[Cell | DFF] = []
    for i, yvar in y.items():
        if yvar.X > 0.5:
            res.append(cells[i])
    for i, zvar in z.items():
        if zvar.X > 0.5:
            res.append(dffs[i])

    return db_to_json(db, res, name)

def extract_dsps_by_count(db: NetlistDB, name: str, count: int, cost_model: Callable, verbose: bool = False) -> dict:
    """
    Extract DSPs by a fixed count.
    It guarantees that the number of DSPs extracted is no more than `count`.
    No need to call greedy.fix_dsps() ahead.
    """
    cells, dffs = db_to_normalized(db, cost_model)

    dsp_tables = db.tables_startswith(name)
    for dsp_table in dsp_tables:
        cur = db.execute(f"SELECT rowid, * FROM {dsp_table}")
        cells.update(Cell(table=dsp_table, rowid=row[0], inputs=set(",".join(row[2:-1]).split(",")), outputs=set(row[-1].split(",")), cost=0) for row in cur)

    cells, dffs = list(cells), list(dffs)
    input, output = {-1, 0, 1}, set()   # DC, GND and VCC are always inputs
    cur.execute("SELECT wire FROM ports WHERE direction = 'input'")
    for (wire,) in cur.fetchall():
        input.update(wire.split(","))
    cur.execute("SELECT wire FROM ports WHERE direction = 'output'")
    for (wire,) in cur.fetchall():
        output.update(wire.split(","))

    # blackbox inputs and outputs
    cur.execute("SELECT wire FROM instance_ports")
    for (wire,) in cur:
        for bit in wire.split(","):
            found = False
            for cell in cells:
                if bit in cell.outputs:
                    output.add(bit)
                    found = True
                    break
            if not found:
                for dff in dffs:
                    if bit in dff.q:
                        output.add(bit)
                        found = True
                        break
            if not found:
                for cell in cells:
                    if bit in cell.inputs:
                        input.add(bit)
                        found = True
                        break
            if not found:
                for dff in dffs:
                    if bit in dff.d or bit in dff.clk:
                        input.add(bit)
                        found = True
                        break
            if not found:
                if bit in output:
                    input.add(bit)
                elif bit in input:
                    output.add(bit)

    bundles = [input, output]
    bundles += [cell.inputs for cell in cells]
    bundles += [cell.outputs for cell in cells]
    bundles += [dff.d for dff in dffs]
    bundles += [dff.clk for dff in dffs]
    bundles += [dff.q for dff in dffs]

    # from collections import Counter
    # # set size
    # sets = Counter(len(bundle) for bundle in bundles)
    # for k, v in sets.items():
    #     print(f"Number of bundles with {k} wires: {v}")
    # # element frequency
    # element_freq = Counter()
    # for bundle in bundles:
    #     element_freq.update(bundle)
    # for k, v in element_freq.most_common(10):
    #     print(f"Element {k} appears in {v} bundles.")
    # return {}

    # print(before, "cells before pruning")   # 30804
    # _prune_cells(cells)
    _prune_cells_fast(cells)
    # groups = list(_group_wires(bundles))    # this also modifies the input bundles into groups
    groups = list(_group_wires_fast(bundles))

    # call gurobi to solve it
    ilp_model = grb.Model("egraph_extraction")
    ilp_model.setParam("OutputFlag", verbose) # silent
    x = ilp_model.addVars(len(groups), vtype=grb.GRB.BINARY, name="x") # choices of wires
    y = ilp_model.addVars(len(cells), vtype=grb.GRB.BINARY, name="y") # choices of cells
    z = ilp_model.addVars(len(dffs), vtype=grb.GRB.BINARY, name="z") # choices of dffs

    def gname_to_index(name: str) -> int:
        return int(name[5:])

    # output constraints
    phase_time = time.time()
    ilp_model.addConstrs((x[gname_to_index(group)] >= 1 for group in output), "output_constraints")
    # for group in output:
    #     ilp_model.addConstr(x[gname_to_index(group)] >= 1, f"output_{group}_constraint")
    print(f"Output constraints added in {time.time() - phase_time:.2f} seconds.")

    # wire constraints
    phase_time = time.time()
    ilp_model.addConstrs((grb.quicksum(y[i] for i in range(len(cells)) if group in cells[i].outputs) + grb.quicksum(z[i] for i in range(len(dffs)) if group in dffs[i].q) >= x[gname_to_index(group)] for group in groups if group not in input), "wire_constraints")
    # for group in groups:
    #     if group not in input:  # if the wire is not an input, it can be chosen or not
    #         # if the wire is chosen, at least one of the cells or dffs must be chosen
    #         ilp_model.addConstr(grb.quicksum(y[i] for i in range(len(cells)) if group in cells[i].outputs) + grb.quicksum(z[i] for i in range(len(dffs)) if group in dffs[i].q) >= x[gname_to_index(group)], f"wire_{group}_constraint")
    print(f"Wire constraints added in {time.time() - phase_time:.2f} seconds.")

    # cell constraints
    phase_time = time.time()
    for i, cell in enumerate(cells):
        for group in cell.inputs:
            ilp_model.addConstr(x[gname_to_index(group)] >= y[i], f"cell_{i}_input_{group}_constraint")    # if the cell is chosen, all its inputs must be chosen
    print(f"Cell constraints added in {time.time() - phase_time:.2f} seconds.")

    # dff constraints
    phase_time = time.time()
    for i, dff in enumerate(dffs):
        for group in dff.d:
            ilp_model.addConstr(x[gname_to_index(group)] >= z[i], f"dff_{i}_input_{group}_constraint")  # if the dff is chosen, all its inputs must be chosen
        for group in dff.clk:
            ilp_model.addConstr(x[gname_to_index(group)] >= z[i], f"dff_{i}_clk_{group}_constraint")    # if the dff is chosen, all its clocks must be chosen
    print(f"DFF constraints added in {time.time() - phase_time:.2f} seconds.")

    # dsp count constraint
    phase_time = time.time()
    ilp_model.addConstr(grb.quicksum(y[i] for i in range(len(cells)) if cells[i].table.startswith(name)) <= count, "dsp_count_constraint")
    print(f"DSP count constraint added in {time.time() - phase_time:.2f} seconds.")

    ilp_model.setParam("MIPGap", 0.05)  # accept 5% gap
    ilp_model.setObjective(
        grb.quicksum(y[i] * cells[i].cost for i in range(len(cells))) +
        grb.quicksum(z[i] * dffs[i].cost for i in range(len(dffs))),
        grb.GRB.MINIMIZE
    )   # minimize the total cost

    ilp_model.write("egraph_extraction.lp")
    ilp_model.optimize()

    if ilp_model.status == grb.GRB.INFEASIBLE:
        raise ValueError("ILP model is infeasible, no solution found.")
    if ilp_model.status == grb.GRB.UNBOUNDED:
        raise ValueError("ILP model is unbounded, no solution found.")
    print(f"ILP model solved with objective value: {ilp_model.objVal}")

    # extract the solution
    res: list[Cell | DFF] = []
    for i, yvar in y.items():
        if yvar.X > 0.5:
            res.append(cells[i])
    for i, zvar in z.items():
        if zvar.X > 0.5:
            res.append(dffs[i])

    return db_to_json(db, res, name)