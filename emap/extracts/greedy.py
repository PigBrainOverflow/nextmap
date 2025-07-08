from ..db import NetlistDB
from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    table: str
    rowid: int
    inputs: set[str]
    outputs: set[str]
    cost: float

    def __hash__(self):
        return hash((self.table, self.rowid))

    def __eq__(self, other):
        if not isinstance(other, Cell):
            return NotImplemented
        return (self.table, self.rowid) == (other.table, other.rowid)

@dataclass(frozen=True)
class DFF:
    rowid: int
    d: set[str]
    clk: set[str]
    q: set[str]
    cost: float

    def __hash__(self):
        return hash(self.rowid)

    def __eq__(self, other):
        if not isinstance(other, DFF):
            return NotImplemented
        return self.rowid == other.rowid

def _cell_to_json(db: NetlistDB, cell: Cell, name: str) -> dict:
    """
    Convert a Cell object to JSON format.
    """
    cur = db.execute(f"SELECT * FROM {cell.table} WHERE rowid = ?", (cell.rowid,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"Cell {cell.table}{cell.rowid} not found in the database.")

    if cell.table == "aby_cells":
        type_, a, b, y = row
        if not type_.endswith(("s", "u")):
            raise ValueError(f"Unsupported cell type: {type_}")
        is_signed = type_.endswith("s")
        return {
            "hide_name": 1,
            "type": type_[:-1],  # remove 's' or 'u'
            "parameters": {
                "A_SIGNED": f"{is_signed:032b}",
                "B_SIGNED": f"{is_signed:032b}",
                "A_WIDTH": f"{NetlistDB.width_of(a):032b}",
                "B_WIDTH": f"{NetlistDB.width_of(b):032b}",
                "Y_WIDTH": f"{NetlistDB.width_of(y):032b}"
            },
            "port_directions": {
                "A": "input",
                "B": "input",
                "Y": "output"
            },
            "connections": {
                "A": NetlistDB.to_bits(a),
                "B": NetlistDB.to_bits(b),
                "Y": NetlistDB.to_bits(y)
            }
        }
    elif cell.table.startswith(name):
        col_names = [desc[0] for desc in cur.description]
        return {
            # for simplicity, we omit signed/zero-extension
            "hide_name": 1,
            "type": cell.table,
            "parameters": {},
            "port_directions": {col_name: "input" for col_name in col_names[1:-1]} | {col_names[-1]: "output"}, # last column is output
            "connections": {col_name: NetlistDB.to_bits(row[i]) for i, col_name in enumerate(col_names[1:], start=1)}
        }
    else:
        # TODO: handle other cell types
        raise ValueError(f"Unsupported cell table: {cell.table}")

def _dff_to_json(db: NetlistDB, dff: DFF) -> dict:
    """
    Convert a DFF object to JSON format.
    """
    cur = db.execute("SELECT d, clk, q FROM dffs WHERE rowid = ?", (dff.rowid,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"DFF with rowid {dff.rowid} not found in the database.")

    d, clk, q = row
    return {
        "hide_name": 1,
        "type": "$dff",
        "parameters": {
            "CLK_POLARITY": "1",  # assuming positive clock polarity
            "WIDTH": f"{NetlistDB.width_of(d):032b}",
        },
        "port_directions": {
            "D": "input",
            "CLK": "input",
            "Q": "output"
        },
        "connections": {
            "D": NetlistDB.to_bits(d),
            "CLK": NetlistDB.to_bits(clk),
            "Q": NetlistDB.to_bits(q)
        }
    }

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

def _db_to_json(db: NetlistDB, choices: list[Cell | DFF], name: str) -> dict:
    mod = {}

    # build ports
    cur = db.execute("SELECT * FROM ports")
    mod["ports"] = {name: {"direction": direction, "bits": NetlistDB.to_bits(wire)} for name, wire, direction in cur}

    # build cells
    mod["cells"] = {}
    for choice in choices:
        if isinstance(choice, Cell):
            mod["cells"][f"{choice.table}{choice.rowid}"] = _cell_to_json(db, choice, name)
        else:   # DFF
            mod["cells"][f"$dff{choice.rowid}"] = _dff_to_json(db, choice)

    # it's ok without netnames
    return mod

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

    cells: set[Cell] = set()
    cur.execute("SELECT rowid, * FROM ay_cells")
    cells.update(Cell(table="ay_cells", rowid=rowid, inputs=set(a.split(",")), outputs=set(y.split(",")), cost=cost_model((type_, a, y))) for rowid, type_, a, y in cur)
    cur.execute("SELECT rowid, * FROM aby_cells")
    cells.update(Cell(table="aby_cells", rowid=rowid, inputs=set(",".join((a, b)).split(",")), outputs=set(y.split(",")), cost=cost_model((type_, a, b, y))) for rowid, type_, a, b, y in cur)
    cur.execute("SELECT rowid, * FROM absy_cells")
    cells.update(Cell(table="absy_cells", rowid=rowid, inputs=set(",".join((a, b, s)).split(",")), outputs=set(y.split(",")), cost=cost_model((type_, a, b, s, y))) for rowid, type_, a, b, s, y in cur)

    cur.execute("SELECT rowid, d, clk, q FROM dffs")
    dffs: set[DFF] = {DFF(rowid=rowid, d=set(d.split(",")), clk=clk, q=set(q.split(",")), cost=cost_model(("$dff", d, clk, q))) for rowid, d, clk, q in cur}

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
                cost_per_progress = float(cell.cost) / len(cell.outputs - reachable)
                if cost_per_progress < choice[0]:   # update choice
                    choice = (cost_per_progress, cell)
        if choice[1] is None:   # cells cannot make progress, consider DFFs
            choice = (float("inf"), None)   # (cost_per_progress, dff)
            for dff in dffs:
                cost_per_progress = float(dff.cost) * len(dff.d - reachable - dff.q) / len(dff.q - reachable)   # cost * (inputs not reachable) / (outputs not reachable)
                if cost_per_progress < choice[0]:   # update choice
                    choice = (cost_per_progress, dff)
            if choice[1] is None:   # no DFFs can make progress
                raise ValueError("No more cells or DFFs can make progress towards the targets.")
            else:
                # add DFF outputs to reachable
                reachable.update(choice[1].q)
                # add DFF inputs to targets
                targets.update(choice[1].d - reachable - dff.q)
                res.append(choice[1])
                dffs.remove(choice[1])
        else:
            # add the cell to reachable
            reachable.update(choice[1].outputs)
            res.append(choice[1])
            cells.remove(choice[1])
            # remove the cell's outputs from targets
            targets -= choice[1].outputs

    return _db_to_json(db, res, name)