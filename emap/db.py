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

    def __init__(self, schema_file: str, db_file: str):
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        self.cnt = 0

    def build_from_json(self, mod: dict):
        ports: dict = mod["ports"]
        cells: dict = mod["cells"]

        # build ports
        db_ports = [(name, NetlistDB.to_str(port["bits"]), port["direction"]) for name, port in ports.items()]
        self.executemany("INSERT INTO ports (name, wire, direction) VALUES (?, ?, ?)", db_ports)

        # build cells
        for cell in cells.values():
            type_: str = cell["type"]
            params: dict = cell["parameters"]
            if type_ in {"$and", "$or", "$xor", "$add", "$sub", "$mul"}:
                type_ += "s" if int(params["A_SIGNED"], base=2) and int(params["B_SIGNED"], base=2) else "u"
                a, b, y = NetlistDB.to_str(cell["connections"]["A"]), NetlistDB.to_str(cell["connections"]["B"]), NetlistDB.to_str(cell["connections"]["Y"])
                self.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, y))
            elif type_ == "$dff":
                if not int(params["CLK_POLARITY"], base=2):
                    raise ValueError("$dff with negative clock polarity is not supported")
                d, clk, q = NetlistDB.to_str(cell["connections"]["D"]), NetlistDB.to_str(cell["connections"]["CLK"]), NetlistDB.to_str(cell["connections"]["Q"])
                self.execute("INSERT OR IGNORE INTO dffs (d, clk, q) VALUES (?, ?, ?)", (d, clk, q))
            elif not type_.startswith("$"): # an instance
                pass
            else:
                raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()