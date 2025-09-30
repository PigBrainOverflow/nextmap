import sqlite3
import json
from typing import Any
from . import utils


class NetlistDB(sqlite3.Connection):
    _db_file: str
    _cnt: int
    _rhash: utils.RollingHash

    @property
    def auto_id(self) -> int:
        self._cnt += 1
        return self._cnt

    @staticmethod
    def bit_to_int(bit: str | int) -> int:
        return -1 if bit == "x" else int(bit)

    def _get_wirevec(self, id: int) -> list[int]:
        cur = self.execute("SELECT wire FROM wirevec_members WHERE wirevec = ? ORDER BY idx", (id,))
        return [w for (w,) in cur]

    def _add_wirevec(self, wv: list[int]) -> int:
        h = self._rhash.hash(wv)
        cur = self.execute("INSERT INTO wirevecs (hash) VALUES (?) RETURNING id", (h,))
        id = cur.fetchone()[0]
        self.executemany(
            "INSERT INTO wirevec_members (wirevec, idx, wire) VALUES (?, ?, ?)",
            ((id, i, w) for i, w in enumerate(wv))
        )
        self.commit()
        return id

    def _create_or_lookup_wirevec(self, wv: list[int]) -> int:
        h = self._rhash.hash(wv)
        cur = self.execute("SELECT id FROM wirevecs WHERE hash = ?", (h,))
        rows = cur.fetchall()
        for (id,) in rows:  # lookup
            if self._get_wirevec(id) == wv:
                return id
        # not found, insert
        cur.execute("INSERT INTO wirevecs (hash) VALUES (?) RETURNING id", (h,))
        id = cur.fetchone()[0]
        self.executemany(
            "INSERT INTO wirevec_members (wirevec, idx, wire) VALUES (?, ?, ?)",
            ((id, i, w) for i, w in enumerate(wv))
        )
        self.commit()
        return id

    def _add_input(self, name: str, source: list[int]):
        ws = self._create_or_lookup_wirevec(source)
        self.execute("INSERT INTO from_inputs (source, name) VALUES (?, ?)", (ws, name))
        self.commit()

    def _add_output(self, name: str, sink: list[int]):
        ws = self._create_or_lookup_wirevec(sink)
        self.execute("INSERT INTO as_outputs (sink, name) VALUES (?, ?)", (ws, name))
        self.commit()

    def __init__(self, schema_file: str, db_file: str = ":memory:", cnt: int = 0):
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        # self.execute("PRAGMA foreign_keys = ON")    # enable foreign key enforcement
        self._db_file = db_file
        self._cnt = cnt
        self._rhash = utils.RollingHash()

    def dump_tables(self) -> dict:
        # get all tables except sqlite internal tables
        cur = self.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';")
        db = {}
        for (table,) in cur.fetchall():
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            db[table] = [dict(zip([col[0] for col in cur.description], row)) for row in rows]
        return db

    def build_from_json(self, mod: dict[str, Any]):
        # NOTE: This is a simplified version of emap build
        # No FFs, no memories, no blackboxes
        # Only combinational logic
        ports: dict[str, Any] = mod["ports"]
        cells: dict[str, Any] = mod["cells"]

        # build inputs & outputs
        for name, port in ports.items():
            direction, bits = port["direction"], [self.bit_to_int(bit) for bit in port["bits"]]
            if direction == "input":
                self._add_input(name, bits)
            elif direction == "output":
                self._add_output(name, bits)
            else:
                raise ValueError(f"Unsupported port direction: {direction}")

        # build cells
        print(f"Found {len(cells)} cells")
        for i, (name, cell) in enumerate(cells.items()):
            if i % 1000 == 0:
                print(f"Processing cell {i}/{len(cells)}: {name}")
            type_: str = cell["type"]
            params: dict[str, Any] = cell["parameters"]
            conns: dict[str, Any] = cell["connections"]

            # ay_cells
            if type_ in {"$not"}:
                awv = [self.bit_to_int(bit) for bit in conns["A"]]
                ywv = [self.bit_to_int(bit) for bit in conns["Y"]]
                assert len(awv) == len(ywv)
                for a, y in zip(awv, ywv):
                    self.execute("INSERT INTO ay_cells (type, a, y) VALUES (?, ?, ?)", (type_, a, y))

            # aby_cells
            elif type_ in {"$and", "$or", "$xor"}:
                awv = [self.bit_to_int(bit) for bit in conns["A"]]
                bwv = [self.bit_to_int(bit) for bit in conns["B"]]
                ywv = [self.bit_to_int(bit) for bit in conns["Y"]]
                assert len(awv) == len(bwv) == len(ywv)
                for a, b, y in zip(awv, bwv, ywv):
                    self.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, y))

            # muxes
            elif type_ in {"$mux"}:
                awv = [self.bit_to_int(bit) for bit in conns["A"]]
                bwv = [self.bit_to_int(bit) for bit in conns["B"]]
                swv = [self.bit_to_int(bit) for bit in conns["S"]]
                ywv = [self.bit_to_int(bit) for bit in conns["Y"]]
                assert len(swv) == 1 and len(awv) == len(bwv) == len(ywv)
                s = swv[0]
                for a, b, y in zip(awv, bwv, ywv):
                    self.execute("INSERT INTO muxes (a, b, s, y) VALUES (?, ?, ?, ?)", (a, b, s, y))

            # arith_aby_cells
            elif type_ in {"$add", "$sub", "$mul"}:
                awv = [self.bit_to_int(bit) for bit in conns["A"]]
                bwv = [self.bit_to_int(bit) for bit in conns["B"]]
                ywv = [self.bit_to_int(bit) for bit in conns["Y"]]
                signed = params["A_SIGNED"] and params["B_SIGNED"]

            else:
                raise ValueError(f"Unsupported cell type: {type_}")