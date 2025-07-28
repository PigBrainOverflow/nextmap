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

def db_to_normalized(db: NetlistDB, cost_model) -> tuple[set[Cell], set[DFF]]:
    cells: set[Cell] = set()
    cur = db.execute("SELECT rowid, * FROM ay_cells")
    cells.update(Cell(table="ay_cells", rowid=rowid, inputs=set(a.split(",")), outputs=set(y.split(",")), cost=cost_model((type_, a, y))) for rowid, type_, a, y in cur)
    cur.execute("SELECT rowid, * FROM aby_cells")
    cells.update(Cell(table="aby_cells", rowid=rowid, inputs=set(",".join((a, b)).split(",")), outputs=set(y.split(",")), cost=cost_model((type_, a, b, y))) for rowid, type_, a, b, y in cur)
    cur.execute("SELECT rowid, * FROM absy_cells")
    cells.update(Cell(table="absy_cells", rowid=rowid, inputs=set(",".join((a, b, s)).split(",")), outputs=set(y.split(",")), cost=cost_model((type_, a, b, s, y))) for rowid, type_, a, b, s, y in cur)

    cur.execute("SELECT rowid, d, clk, q FROM dffs")
    dffs: set[DFF] = {DFF(rowid=rowid, d=set(d.split(",")), clk={clk}, q=set(q.split(",")), cost=cost_model(("$dff", d, clk, q))) for rowid, d, clk, q in cur}

    return cells, dffs

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
            return {
                "hide_name": 1,
                "type": type_,
                "parameters": {},
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
    elif cell.table == "ay_cells":
        type_, a, y = row
        if type_ not in {"$not", "$logic_not"}:
            raise ValueError(f"Unsupported cell type: {type_}")
        return {
            "hide_name": 1,
            "type": type_,
            "parameters": {
                "A_WIDTH": f"{NetlistDB.width_of(a):032b}",
                "Y_WIDTH": f"{NetlistDB.width_of(y):032b}"
            },
            "port_directions": {
                "A": "input",
                "Y": "output"
            },
            "connections": {
                "A": NetlistDB.to_bits(a),
                "Y": NetlistDB.to_bits(y)
            }
        }
    elif cell.table == "absy_cells":
        type_, a, b, s, y = row
        if type_ != "$mux":
            raise ValueError(f"Unsupported cell type: {type_}")
        return {
            "hide_name": 1,
            "type": type_,
            "parameters": {
                "A_WIDTH": f"{NetlistDB.width_of(a):032b}",
                "B_WIDTH": f"{NetlistDB.width_of(b):032b}",
                "S_WIDTH": f"{NetlistDB.width_of(s):032b}",
                "Y_WIDTH": f"{NetlistDB.width_of(y):032b}"
            },
            "port_directions": {
                "A": "input",
                "B": "input",
                "S": "input",
                "Y": "output"
            },
            "connections": {
                "A": NetlistDB.to_bits(a),
                "B": NetlistDB.to_bits(b),
                "S": NetlistDB.to_bits(s),
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

def db_to_json(db: NetlistDB, choices: list[Cell | DFF], name: str) -> dict:
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

    # build blackboxes
    cur = db.execute("SELECT id, module FROM instances")
    for id, module in cur:
        params = {param: val for param, val in db.execute("SELECT param, val FROM instance_params WHERE instance = ?", (id,))}
        conns = {port: NetlistDB.to_bits(wire) for port, wire in db.execute("SELECT port, wire FROM instance_ports WHERE instance = ?", (id,))}
        blackbox = {
            "hide_name": 1,
            "type": module,
            "parameters": params,
            "attributes": {"module_not_derived": f"{1:032b}"},
            "connections": conns
        }
        mod["cells"][id] = blackbox

    # it's ok without netnames
    return mod