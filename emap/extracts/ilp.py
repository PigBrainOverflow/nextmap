from ..db import NetlistDB
from .utils import Cell, DFF, db_to_normalized
from typing import Iterable
import gurobipy as grb


def _group_wires(bundles: Iterable[set]) -> dict[str, set]:
    """
    Return a dictionary mapping each wire group to its corresponding set of wires.
    Modifies the input list of wires in place.
    For example, if bundles = [{1,2}, {1,2,3}, {3,4}], the output will be: [{1,2}, {3}, {4}].
    In most cases, this can significantly reduce the number of wires
    """
    groups = {}
    cnt = 0
    wires = set()
    for bundle in bundles:
        wires.update(bundle)

    for wire in wires:
        wire_group = set()
        for bundle in bundles:
            if wire in bundle:
                wire_group = wire_group.intersection(bundle) if wire_group else {w for w in bundle if not isinstance(w, str) or not w.startswith("group")}
        if not wire_group:  # this wire is not in any bundle
            continue
        groups[f"group{cnt}"] = wire_group
        # update bundles
        for bundle in bundles:
            if wire_group <= bundle:
                bundle -= wire_group
                bundle.add(f"group{cnt}")
        cnt += 1

    return groups

def extract_dsps(db: NetlistDB, name: str, cost_model) -> dict:
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
    groups = list(_group_wires(bundles))
    print(input, output, cells, dffs)

    # call gurobi to solve it
    ilp_model = grb.Model("egraph_extraction")
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

    return {}