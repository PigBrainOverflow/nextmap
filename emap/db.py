import sqlite3
from typing import Iterable


class NetlistDB(sqlite3.Connection):
    cnt: int

    # auxiliary functions
    @staticmethod
    def to_str(v: Iterable) -> str:
        return ",".join(str(x) for x in v)

    @staticmethod
    def width_of(s: str) -> int:
        return s.count(",") + 1 if s else 0

    def next_wire(self) -> str:
        self.cnt += 1
        return f"tmp{self.cnt}"

    def next_wires(self, n: int) -> str:
        return ",".join(self.next_wire() for _ in range(n))

    def __init__(self, schema_file: str, db_file: str):
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        self.cnt = 0
        self.create_function("width_of", 1, NetlistDB.width_of)

    def build_from_json(self, mod: dict):
        ports: dict = mod["ports"]
        cells: dict = mod["cells"]

        # build ports
        db_ports = [(name, NetlistDB.to_str(port["bits"]), port["direction"]) for name, port in ports.items()]
        self.executemany("INSERT OR IGNORE INTO ports (name, wire, direction) VALUES (?, ?, ?)", db_ports)

        # build cells
        for cell in cells.values():
            type_: str = cell["type"]
            params: dict = cell["parameters"]
            conns: dict = cell["connections"]
            if type_ in {"$and", "$or", "$xor", "$add", "$sub", "$mul"}:
                type_ += "s" if int(params["A_SIGNED"], base=2) and int(params["B_SIGNED"], base=2) else "u"
                a, b, y = NetlistDB.to_str(conns["A"]), NetlistDB.to_str(conns["B"]), NetlistDB.to_str(conns["Y"])
                self.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, y))
            elif type_ == "$dff":
                if not int(params["CLK_POLARITY"], base=2):
                    raise ValueError("$dff with negative clock polarity is not supported")
                d, clk, q = NetlistDB.to_str(conns["D"]), NetlistDB.to_str(conns["CLK"]), NetlistDB.to_str(conns["Q"])
                self.execute("INSERT OR IGNORE INTO dffs (d, clk, q) VALUES (?, ?, ?)", (d, clk, q))
            elif type_ == "$mux":
                a, b, s, y = NetlistDB.to_str(conns["A"]), NetlistDB.to_str(conns["B"]), NetlistDB.to_str(conns["S"]), NetlistDB.to_str(conns["Y"])
                self.execute("INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)", ("$mux", a, b, s, y))
            elif not type_.startswith("$"): # an instance
                pass
            else:
                raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()

    def dump_tables(self) -> dict:
        # get all tables
        cur = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        db = {}
        for (table,) in cur.fetchall():
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            db[table] = [dict(zip([col[0] for col in cur.description], row)) for row in rows]

        return db