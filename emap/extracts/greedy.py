from ..db import NetlistDB
from .utils import Cell, DFF, db_to_normalized, db_to_json


def _delete_subset_rows(db: NetlistDB, table: str, output: str, wires: set[str]):
    """
    Delete rows in the specified table where the output wires are a subset of the given wires.
    """
    # this is a helper function to delete rows in the same eclass
    # costly since it requires a full scan of the table
    cur = db.execute(f"SELECT rowid, {output} FROM {table}")
    for row in cur.fetchall():
        if set(row[1].split(",")) <= wires:
            db.execute(f"DELETE FROM {table} WHERE rowid = ?", (row[0],))

def fix_one_dsp(db: NetlistDB, name: str) -> int:
    """
    Return the largest value of the DSP.
    0 if no DSP is found.
    """
    tables = db.tables_startswith(name)

    # for each table, find the row with largest value
    largest = (0, None, None)   # (value, row, table)
    for table in tables:
        cur = db.execute(f"SELECT rowid, * FROM {table} ORDER BY value DESC LIMIT 1")
        row = cur.fetchone()
        if row is not None and row[1] > largest[0]:
            largest = (row[1], row, table)

    if largest[0] > 0 and largest[1] is not None:
        _, row, table = largest
        # first, remove all rows with the same or subset output (in the same eclass)
        # suppose `output` is in the last column
        output_wires = set(row[-1].split(","))
        _delete_subset_rows(db, "aby_cells", "y", output_wires)
        _delete_subset_rows(db, "dffs", "q", output_wires)
        for table_ in tables:
            _delete_subset_rows(db, table_, "out", output_wires)
        # then, insert the row with value 0
        db.execute(f"INSERT INTO {table} VALUES ({','.join(['?'] * (len(row) - 1))})", (0, *row[2:]))
        db.commit()

    return largest[0]

def fix_dsps(db: NetlistDB, name: str, count: int = 1) -> list[int]:
    """
    Fix multiple DSPs by calling `fix_one_dsp` repeatedly.
    Return the values of the fixed DSPs.
    """
    fixed_values = []
    for _ in range(count):
        value = fix_one_dsp(db, name)
        if value > 0:
            fixed_values.append(value)
        else:
            break
    return fixed_values

def extract_dsps_bottom_up(db: NetlistDB, name: str, cost_model) -> dict:
    """
    Return the JSON format of the module.
    Simple bottom-up extraction algorithm.
    WARNING: Unable to handle blackboxes, but can be supported in the future.
    """
    reachable: set[str] = set()
    targets: set[str] = set()

    # first, add all inputs to reachable and all outputs to targets
    cur = db.execute("SELECT wire FROM ports WHERE direction = 'input'")
    for (input,) in cur.fetchall():
        reachable.update(input.split(","))
    cur.execute("SELECT wire FROM ports WHERE direction = 'output'")
    for (output,) in cur.fetchall():
        targets.update(output.split(","))
    targets -= reachable

    cells, dffs = db_to_normalized(db, cost_model)

    # it's also possible to let users define the cost model for DSPs
    # for simplicity, we only consider the DSPs that are already fixed
    dsp_tables = db.tables_startswith(name)
    for dsp_table in dsp_tables:
        cur.execute(f"SELECT rowid, * FROM {dsp_table} WHERE value = 0")
        cells.update(Cell(table=dsp_table, rowid=row[0], inputs=set(",".join(row[2:-1]).split(",")), outputs=set(row[-1].split(",")), cost=0) for row in cur)

    res: list[Cell | DFF] = []
    while targets:  # while there are still targets to reach
        # try to make heuristically biggest progress by adding a cell
        choice = (float("inf"), None)   # (cost_per_progress, cell)
        for cell in cells:
            if cell.inputs <= reachable:    # reachable
                diff = len(cell.outputs - reachable)  # how many outputs can be reached
                if diff == 0:   # no progress can be made
                    continue
                cost_per_progress = float(cell.cost) / diff
                if cost_per_progress < choice[0]:   # update choice
                    choice = (cost_per_progress, cell)
        if choice[1] is None:   # cells cannot make progress, consider DFFs
            choice = (float("inf"), None)   # (cost_per_progress, dff)
            for dff in dffs:
                diff = len(dff.q - reachable)
                if diff == 0:
                    continue
                cost_per_progress = float(dff.cost) * len(dff.d - reachable - dff.q) / diff # cost * (inputs not reachable) / (outputs not reachable)
                if cost_per_progress < choice[0]:   # update choice
                    choice = (cost_per_progress, dff)
            if choice[1] is None:   # no DFFs can make progress
                raise ValueError("No more cells or DFFs can make progress towards the targets.")
            else:
                # add DFF outputs to reachable
                reachable.update(choice[1].q)
                # add DFF inputs to targets
                targets.update(choice[1].d - reachable)
                # remove DFF outputs from targets
                targets -= choice[1].q
                res.append(choice[1])
                dffs.remove(choice[1])
        else:
            # add the cell to reachable
            reachable.update(choice[1].outputs)
            res.append(choice[1])
            cells.remove(choice[1])
            # remove the cell's outputs from targets
            targets -= choice[1].outputs

    # NOTE: alternatively, call yosys command `clean -purge` to do this for you
    # at the end, we need to prune some wires that are not used and driven more than once
    # changed = True
    # while changed:
    #     changed = False
    #     used = set()
    #     for cell in res:
    #         if isinstance(cell, Cell):
    #             used.update(cell.inputs if isinstance(cell, Cell) else cell.d)
    #     for cell in res:
    #         if isinstance(cell, Cell):
    #             if not (cell.outputs & used):
    #                 res.remove(cell)
    #                 changed = True

    return db_to_json(db, res, name)