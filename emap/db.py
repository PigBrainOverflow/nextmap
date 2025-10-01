import sqlite3
from typing import Any
from . import utils


class NetlistDB(sqlite3.Connection):
    VERBOSE: bool = False
    _db_file: str
    _cnt: int
    _xhash: utils.XorHash

    @property
    def auto_id(self) -> int:
        self._cnt += 1
        return self._cnt

    @staticmethod
    def bit_to_int(bit: str | int) -> int:
        return -1 if bit == "x" else int(bit)

    @staticmethod
    def int_to_bit(val: int) -> int | str:
        if val == -1:
            return "x"
        if val in {0, 1}:
            return str(val)
        return val

    # @staticmethod
    # def param_to_int(param: str | int) -> int:
    #     return param if isinstance(param, int) else int(param, base=2)

    def _get_wireset(self, id: int) -> set[int]:
        cur = self.execute("SELECT wire FROM wiresets_members WHERE wireset_id = ?", (id,))
        return {w for (w,) in cur}

    def _add_wireset(self, ws: set[int]) -> int:
        h = self._xhash.hash(ws)
        cur = self.execute("INSERT INTO wiresets (hash) VALUES (?) RETURNING id", (h,))
        id = cur.fetchone()[0]
        self.executemany(
            "INSERT INTO wiresets_members (wireset_id, wire) VALUES (?, ?)",
            ((id, w) for w in ws)
        )
        self.commit()
        return id

    def _create_or_lookup_wireset(self, ws: set[int]) -> int:
        h = self._xhash.hash(ws)
        cur = self.execute("SELECT id FROM wiresets WHERE hash = ?", (h,))
        rows = cur.fetchall()
        for (id,) in rows:  # lookup
            if self._get_wireset(id) == ws:
                return id
        # not found, insert
        cur.execute("INSERT INTO wiresets (hash) VALUES (?) RETURNING id", (h,))
        id = cur.fetchone()[0]
        self.executemany(
            "INSERT INTO wiresets_members (wireset_id, wire) VALUES (?, ?)",
            ((id, w) for w in ws)
        )
        self.commit()
        return id

    def _add_input(self, name: str, source: int):
        self.execute("INSERT INTO from_inputs (source, name) VALUES (?, ?)", (source, name))
        self.commit()

    def _add_output(self, name: str, sink: int):
        self.execute("INSERT INTO as_outputs (sink, name) VALUES (?, ?)", (sink, name))
        self.commit()

    def __init__(self, schema_file: str, db_file: str = ":memory:", cnt: int = 0):
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        # self.execute("PRAGMA foreign_keys = ON")    # enable foreign key enforcement
        self._db_file = db_file
        self._cnt = cnt
        self._xhash = utils.XorHash()

    def dump_tables(self) -> dict:
        # get all tables except sqlite internal tables
        cur = self.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';")
        db = {}
        for (table,) in cur.fetchall():
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            db[table] = [dict(zip([col[0] for col in cur.description], row)) for row in rows]
        return db

    @property
    def inv_cnt(self) -> int:
        cur = self.execute("SELECT COUNT(*) FROM invs")
        return cur.fetchone()[0]

    @property
    def and_cnt(self) -> int:
        cur = self.execute("SELECT COUNT(*) FROM ands")
        return cur.fetchone()[0]

    def build_from_json(self, mod: dict[str, Any]):
        # NOTE: This is a simplified version of emap build.
        # We only accept AIGs with multiple inputs and outputs.
        ports: dict[str, Any] = mod["ports"]
        cells: dict[str, Any] = mod["cells"]

        # build consts
        # self._add_input("VCC", [1]) # VCC is always 1
        # self._add_input("GND", [0]) # GND is always 0
        # self._add_input("DC", [-1]) # DC is always x

        # build inputs & outputs
        for name, port in ports.items():
            bits = port["bits"]
            assert len(bits) == 1
            direction, bit = port["direction"], self.bit_to_int(bits[0])
            assert bit != -1
            if direction == "input":
                self._add_input(name, bit)
            elif direction == "output":
                self._add_output(name, bit)
            else:
                raise ValueError(f"Unsupported port direction: {direction}")

        # build cells
        print(f"Found {len(cells)} cells")
        for i, (name, cell) in enumerate(cells.items()):
            if self.VERBOSE and i % 1000 == 0:
                print(f"Processing cell {i}/{len(cells)}: {name}")
            type_: str = cell["type"]
            conns: dict[str, Any] = cell["connections"]

            # ands
            if type_ == "$and":
                A, B, Y = conns["A"], conns["B"], conns["Y"]
                assert len(A) == len(B) == len(Y) == 1
                a, b, y = self.bit_to_int(A[0]), self.bit_to_int(B[0]), self.bit_to_int(Y[0])
                assert a != -1 and b != -1 and y != -1
                self.execute("INSERT OR IGNORE INTO ands (a, b, y) VALUES (?, ?, ?)", (a, b, y))

            # invs
            elif type_ == "$not":
                A, Y = conns["A"], conns["Y"]
                assert len(A) == len(Y) == 1
                a, y = self.bit_to_int(A[0]), self.bit_to_int(Y[0])
                assert a != -1 and y != -1
                self.execute("INSERT OR IGNORE INTO invs (a, y) VALUES (?, ?)", (a, y))

            else:
                raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()


    """
    Rebuild-related methods
    """
    def _merge_cells(self, dsu: utils.DisjointSetUnion):
        # deduplicate invs
        cur = self.execute("SELECT a, y FROM invs")
        invs_pk: dict[int, list[int]] = {}
        for a, y in cur:
            if a not in invs_pk:
                invs_pk[a] = []
            invs_pk[a].append(y)
        for a, ys in invs_pk.items():
            if len(ys) > 1:
                # remove duplicates
                # we keep the smallest y since it is likely to be the leader and constant
                ys.sort()
                cur.execute("DELETE FROM invs WHERE a = ? AND y != ?", (a, ys[0]))
                for y in ys[1:]:
                    dsu.union(ys[0], y)
        self.commit()

        # deduplicate ands
        cur = self.execute("SELECT a, b, y FROM ands")
        ands_pk: dict[tuple[int, int], list[int]] = {}
        for a, b, y in cur:
            if (a, b) not in ands_pk:
                ands_pk[(a, b)] = []
            ands_pk[(a, b)].append(y)
        for (a, b), ys in ands_pk.items():
            if len(ys) > 1:
                # remove duplicates
                # we keep the smallest y since it is likely to be the leader and constant
                ys.sort()
                cur.execute("DELETE FROM ands WHERE a = ? AND b = ? AND y != ?", (a, b, ys[0]))
                for y in ys[1:]:
                    dsu.union(ys[0], y)
        self.commit()

    def _update_cells(self, wdsu: utils.DisjointSetUnion):
        # propagate wire updates to cells
        for i, w in enumerate(wdsu.parents):
            if self.VERBOSE and i % 1000 == 0:
                print(f"Updating cells for wire {i}/{len(wdsu.parents)}")
            leader = wdsu.find(w)
            if leader != w:
                # update invs
                cur = self.execute("SELECT y FROM invs WHERE a = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM invs WHERE a = ?", (w,))
                cur.executemany("INSERT OR IGNORE INTO invs (a, y) VALUES (?, ?)", ((leader, y) for y in rows))
                cur = self.execute("SELECT type, a FROM invs WHERE y = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM invs WHERE y = ?", (w,))
                cur.executemany("INSERT OR IGNORE INTO invs (a, y) VALUES (?, ?)", ((a, leader) for a in rows))

                # update ands
                cur = self.execute("SELECT b, y FROM ands WHERE a = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ands WHERE a = ?", (w,))
                cur.executemany("INSERT OR IGNORE INTO ands (a, b, y) VALUES (?, ?, ?)", ((leader, b, y) for b, y in rows))
                cur = self.execute("SELECT a, y FROM ands WHERE b = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ands WHERE b = ?", (w,))
                cur.executemany("INSERT OR IGNORE INTO ands (a, b, y) VALUES (?, ?, ?)", ((a, leader, y) for a, y in rows))
                cur = self.execute("SELECT a, b FROM ands WHERE y = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ands WHERE y = ?", (w,))
                cur.executemany("INSERT OR IGNORE INTO ands (a, b, y) VALUES (?, ?, ?)", ((a, b, leader) for a, b in rows))

                # update from_inputs
                self.execute("UPDATE from_inputs SET source = ? WHERE source = ?", (leader, w))
                # update as_outputs
                self.execute("UPDATE as_outputs SET sink = ? WHERE sink = ?", (leader, w))
        self.commit()

    def rebuild_once(self, wdsu: utils.DisjointSetUnion) -> bool:
        # merge_cells -> merge_wires -> merge_wirevecs -> update_cells
        # all phases are batched processing
        self._merge_cells(wdsu)
        if not wdsu.parents:
            return False
        self._update_cells(wdsu)
        return True

    def rebuild(self, wdsu: utils.DisjointSetUnion) -> int:
        cnt = 0
        while self.rebuild_once(wdsu):
            if self.VERBOSE:
                print(f"Rebuild iteration {cnt} done.")
            cnt += 1
            wdsu.parents.clear()    # clear the worklist
        return cnt

    def write_json(self) -> dict[str, Any]:
        """
        Dump the database to json format
        """

        # build ports
        ports: dict[str, dict[str, Any]] = {}
        cur = self.execute("SELECT name, source FROM from_inputs")
        for name, source in cur.fetchall():
            ports[name] = {"direction": "input", "bits": [self.int_to_bit(source)]}
        cur = self.execute("SELECT name, sink FROM as_outputs")
        for name, sink in cur.fetchall():
            ports[name] = {"direction": "output", "bits": [self.int_to_bit(sink)]}

        # build cells
        cells: dict[str, dict[str, Any]] = {}
        cnt = 0
        cur = self.execute("SELECT a, y FROM invs")
        for a, y in cur.fetchall():
            cells[f"cell{cnt}"] = {
                "type": "$not",
                "parameters": {
                    "A_SIGNED": 0,
                    "A_WIDTH": 1,
                    "Y_WIDTH": 1
                },
                "port_directions": {
                    "A": "input",
                    "Y": "output"
                },
                "connections": {
                    "A": [self.int_to_bit(a)],
                    "Y": [self.int_to_bit(y)]
                }
            }
            cnt += 1
        cur = self.execute("SELECT a, b, y FROM ands")
        for a, b, y in cur.fetchall():
            cells[f"cell{cnt}"] = {
                "type": "$and",
                "parameters": {
                    "A_SIGNED": 0,
                    "A_WIDTH": 1,
                    "B_SIGNED": 0,
                    "B_WIDTH": 1,
                    "Y_WIDTH": 1
                },
                "port_directions": {
                    "A": "input",
                    "B": "input",
                    "Y": "output"
                },
                "connections": {
                    "A": [self.int_to_bit(a)],
                    "B": [self.int_to_bit(b)],
                    "Y": [self.int_to_bit(y)]
                }
            }
            cnt += 1

        return {"ports": ports, "cells": cells}