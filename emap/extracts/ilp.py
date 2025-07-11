from ..db import NetlistDB
from .utils import Cell, DFF, db_to_normalized
import gurobipy


def _group_wires(bundles: list[set]) -> dict[str, set]:
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
        cur.execute(f"SELECT rowid, * FROM {dsp_table} WHERE value = 0")
        cells.update(Cell(table=dsp_table, rowid=row[0], inputs=set(",".join(row[2:-1]).split(",")), outputs=set(row[-1].split(",")), cost=0) for row in cur)

    # call gurobi to solve it
    ilp_model = gurobipy.Model("egraph_extraction")
    x = ilp_model.addVars()

    return {}