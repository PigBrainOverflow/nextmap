import sqlite3
from typing import Iterable, Any


class NetlistDB(sqlite3.Connection):
    cnt: int

    # auxiliary functions
    @staticmethod
    def to_str(v: Iterable) -> str:
        return ",".join(str(x) for x in v)

    @staticmethod
    def width_of(s: str) -> int:
        return s.count(",") + 1 if s else 0

    @staticmethod
    def to_bits(s: str) -> list[int | str]:
        return [x if x in {"0", "1", "x"} else int(x) for x in s.split(",")]

    @staticmethod
    def to_int(x: str | int) -> int:
        return x if isinstance(x, int) else int(x, base=2)

    def find_or_create_aby_cell(self, width: int, type_: str, a: str, b: str) -> str:
        """
        Return wire y
        """
        cur = self.execute("SELECT y FROM aby_cells WHERE type = ? AND a = ? AND b = ?", (type_, a, b))
        res = cur.fetchone()
        if res is None:  # not exists
            y = self.next_wires(width)
            self.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, y))
            return y
        else:
            return res[0]

    def find_or_create_dff(self, width: int, d: str, clk: str) -> str:
        """
        Return wire q
        """
        cur = self.execute("SELECT q FROM dffs WHERE d = ? AND clk = ?", (d, clk))
        res = cur.fetchone()
        if res is None:
            q = self.next_wires(width)
            self.execute("INSERT INTO dffs (d, clk, q) VALUES (?, ?, ?)", (d, clk, q))
            return q
        else:
            return res[0]

    def tables_startswith(self, prefix: str) -> list[str]:
        cur = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?;", (prefix + "%",))
        return [row[0] for row in cur.fetchall()]

    def next_wire(self) -> str:
        self.cnt += 1
        return str(self.cnt)

    def next_wires(self, n: int) -> str:
        return ",".join(self.next_wire() for _ in range(n))

    def __init__(self, schema_file: str, db_file: str, cnt: int = 0):
        """
        Arguments:
        - `schema_file`: Path to the SQL schema file.
        - `db_file`: Path to the SQLite database file. Use ":memory:" for an in-memory database.
        - `cnt`: Initial count for wire generation. Defaults to 0.
        """
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        self.cnt = cnt
        self.create_function("width_of", 1, NetlistDB.width_of)

    def build_from_json(self, mod: dict[str, Any]):
        ports: dict = mod["ports"]
        cells: dict = mod["cells"]

        # build ports
        db_ports = [(name, NetlistDB.to_str(port["bits"]), port["direction"]) for name, port in ports.items()]
        self.executemany("INSERT INTO ports (name, wire, direction) VALUES (?, ?, ?)", db_ports)

        # build cells
        for name, cell in cells.items():
            type_: str = cell["type"]
            params: dict = cell["parameters"]
            conns: dict = cell["connections"]
            if type_ in {"$and", "$or", "$xor", "$add", "$sub", "$mul", "$mod"}:
                type_ += "s" if NetlistDB.to_int(params["A_SIGNED"]) and NetlistDB.to_int(params["B_SIGNED"]) else "u"
                a, b, y = NetlistDB.to_str(conns["A"]), NetlistDB.to_str(conns["B"]), NetlistDB.to_str(conns["Y"])
                self.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, y))
            elif type_ == "$dff":
                if not NetlistDB.to_int(params["CLK_POLARITY"]):
                    raise ValueError("$dff with negative clock polarity is not supported")
                d, clk, q = NetlistDB.to_str(conns["D"]), NetlistDB.to_str(conns["CLK"]), NetlistDB.to_str(conns["Q"])
                self.execute("INSERT OR IGNORE INTO dffs (d, clk, q) VALUES (?, ?, ?)", (d, clk, q))
            elif type_ == "$mux":
                a, b, s, y = NetlistDB.to_str(conns["A"]), NetlistDB.to_str(conns["B"]), NetlistDB.to_str(conns["S"]), NetlistDB.to_str(conns["Y"])
                self.execute("INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)", ("$mux", a, b, s, y))
            elif type_ in {"$not", "$logic_not"}:
                a, y = NetlistDB.to_str(conns["A"]), NetlistDB.to_str(conns["Y"])
                self.execute("INSERT OR IGNORE INTO ay_cells (type, a, y) VALUES (?, ?, ?)", (type_, a, y))
            elif type_ in {
                "$eq", "$ge", "$le", "$gt", "$lt",
                "$logic_and", "$logic_or"
            }:
                a, b, y = NetlistDB.to_str(conns["A"]), NetlistDB.to_str(conns["B"]), NetlistDB.to_str(conns["Y"])
                self.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, y))
            else:
                attrs = cell["attributes"]
                if "module_not_derived" in attrs and NetlistDB.to_int(attrs["module_not_derived"]): # blackbox cell
                    self.execute("INSERT INTO instances (id, module) VALUES (?, ?)", (name, type_))
                    self.executemany(
                        "INSERT INTO instance_params (instance, param, val) VALUES (?, ?, ?)",
                        ((name, param, val) for param, val in params.items())
                    )
                    self.executemany(
                        "INSERT INTO instance_ports (instance, port, wire) VALUES (?, ?, ?)",
                        ((name, port, NetlistDB.to_str(conns[port])) for port in conns)
                    )
                else:
                    raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()

    def dump_tables(self) -> dict:
        # get all tables
        cur = self.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';")
        db = {}
        for (table,) in cur.fetchall():
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            db[table] = [dict(zip([col[0] for col in cur.description], row)) for row in rows]

        return db

    def _merge_wire(self, a: str, b: str):
        # merge a to b
        # check aby_cells
        if a == b:
            return
        cur = self.execute("SELECT rowid, a FROM aby_cells WHERE instr(',' || a || ',', ?)", (',' + a + ',',))
        self.executemany(
            "UPDATE OR IGNORE aby_cells SET a = ? WHERE rowid = ?",
            ((("," + a_ + ",").replace("," + a + ",", "," + b + ",")[1:-1], rowid) for rowid, a_ in cur)
        )
        cur.execute("SELECT rowid, b FROM aby_cells WHERE instr(',' || b || ',', ?)", (',' + a + ',',))
        self.executemany(
            "UPDATE OR IGNORE aby_cells SET b = ? WHERE rowid = ?",
            ((("," + b_ + ",").replace("," + a + ",", "," + b + ",")[1:-1], rowid) for rowid, b_ in cur)
        )

    def rebuild(self):
        # TODO: handle blackbox cells correctly
        # not efficient, but works for now
        # NOTE: the best way is to build a table for sequences of integers
        outputs: set[str] = set()   # outputs should be kept
        cur = self.execute("SELECT wire FROM ports WHERE direction = 'output'")
        for (wire,) in cur.fetchall():
            outputs.update(wire.split(","))

        modified = True
        while modified:
            modified = False
            # check aby_cells
            cur.execute("SELECT type, a, b FROM aby_cells GROUP BY type, a, b HAVING COUNT(*) > 1 LIMIT 1")
            res = cur.fetchone()
            if res is not None:
                type_, a, b = res
                cur.execute("SELECT y FROM aby_cells WHERE type = ? AND a = ? AND b = ?", (type_, a, b))
                ys = [row[0].split(",") for row in cur]
                cur.execute("DELETE FROM aby_cells WHERE type = ? AND a = ? AND b = ?", (type_, a, b))
                for i in range(0, len(ys[0])):
                    for y in ys:
                        if y[i] not in outputs:
                            self._merge_wire(y[i], ys[0][i])
                cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, ",".join(ys[0])))
                modified = True