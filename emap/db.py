import sqlite3
import json
from typing import Any
from . import utils


class NetlistDB(sqlite3.Connection):
    _db_file: str
    _clk: int | None
    _cnt: int
    _rhash: utils.RollingHash

    @staticmethod
    def bit_to_int(bit: str | int) -> int:
        return -1 if bit == "x" else int(bit)

    @staticmethod
    def param_to_int(param: str | int) -> int:
        return param if isinstance(param, int) else int(param, base=2)

    @staticmethod
    def width_of(conn: sqlite3.Connection, id) -> int:
        cur = conn.execute("SELECT MAX(idx) FROM wirevec_members WHERE wirevec = ?", (id,))
        return cur.fetchone()[0] + 1

    @staticmethod
    def vec_to_const(vec: list[int]) -> int | None:
        # return None if not a constant vector
        val = 0
        for b in reversed(vec):
            if b not in (0, 1):
                return None
            val = (val << 1) | b
        return val

    @property
    def auto_id(self) -> int:
        self._cnt += 1
        return self._cnt

    @property
    def tech_tables(self) -> list[str]:
        cur = self.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'tech_%';")
        return [name for (name,) in cur]

    def __init__(self, schema_file: str, db_file: str = ":memory:", cnt: int = 0):
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        # self.execute("PRAGMA foreign_keys = ON")    # enable foreign key enforcement
        self._db_file = db_file
        self._clk = None
        self._cnt = cnt
        self._rhash = utils.RollingHash()
        self.create_function("width_of", 1, lambda id: self.width_of(self, id))

    def dump_tables(self) -> dict:
        # get all tables except sqlite internal tables
        cur = self.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';")
        db = {}
        for (table,) in cur.fetchall():
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            db[table] = [dict(zip([col[0] for col in cur.description], row)) for row in rows]
        return db

    def dump_wirevecs(self) -> dict[int, list[int]]:
        cur = self.execute("SELECT id FROM wirevecs")
        wvs = {}
        for (id,) in cur.fetchall():
            wvs[id] = self._get_wirevec(id)
        return wvs

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

    def _add_dff(self, d: list[int], q: list[int]):
        wvd = self._create_or_lookup_wirevec(d)
        wvq = self._create_or_lookup_wirevec(q)
        self.execute("INSERT OR IGNORE INTO dffs (d, q) VALUES (?, ?)", (wvd, wvq))
        self.commit()

    def _add_ay_cell(self, type_: str, a: list[int], y: list[int]):
        wva, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(y)
        self.execute("INSERT OR IGNORE INTO ay_cells (type, a, y) VALUES (?, ?, ?)", (type_, wva, wvy))
        self.commit()

    def _add_aby_cell(self, type_: str, a: list[int], b: list[int], y: list[int]):
        wva, wvb, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(b), self._create_or_lookup_wirevec(y)
        self.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, wva, wvb, wvy))
        self.commit()

    def _add_absy_cell(self, type_: str, a: list[int], b: list[int], s: list[int], y: list[int]):
        wva, wvb, wvs, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(b), self._create_or_lookup_wirevec(s), self._create_or_lookup_wirevec(y)
        self.execute("INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)", (type_, wva, wvb, wvs, wvy))
        self.commit()

    def _add_blackbox_cell(self, name: str, module: str, params: dict[str, Any], signals: list[tuple[str, list[int]]]):
        self.execute("INSERT INTO instances (name, params, module) VALUES (?, ?, ?)", (name, json.dumps(params), module))
        self.executemany("INSERT INTO instance_ports (instance, port, signal) VALUES (?, ?, ?)", ((name, port, self._create_or_lookup_wirevec(signal)) for port, signal in signals))
        self.commit()

    def build_from_json_cpp(self, mod: dict[str, Any], clk: str = "clk"):
        if self._db_file == ":memory:":
            raise RuntimeError("Cannot call build_from_json_cpp() on in-memory database")
        try:
            from .emapcc.build import emapcc
            self._clk, self._cnt = emapcc.build_from_json(self._db_file, mod, clk, self._rhash._POWER_B[1], self._rhash._M)
        except ImportError:
            raise RuntimeError("Module emapcc is not available. Please build emapcc to use build_from_json_cpp()")
        except Exception as e:
            raise RuntimeError(f"Failed to build from JSON: {e}")

    def build_from_json(self, mod: dict[str, Any], clk: str = "clk"):
        # NOTE: only support single global clock
        ports: dict[str, Any] = mod["ports"]
        cells: dict[str, Any] = mod["cells"]

        # build inputs & outputs
        for name, port in ports.items():
            direction, bits = port["direction"], [self.bit_to_int(bit) for bit in port["bits"]]
            if direction == "input":
                if name == clk:
                    if len(bits) != 1:
                        raise ValueError("Clock port must have exactly one bit")
                    self._clk = bits[0]
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
            # TODO: for simplicity, we treat bitwise logic gates as word-level operations
            if type_ in {
                "$and", "$or", "$xor",
                "$shl", "$shr", "$sshr",
                "$add", "$sub", "$mul", "$mod"
            }:
                type_ += "s" if self.param_to_int(params["A_SIGNED"]) and self.param_to_int(params["B_SIGNED"]) else "u"
                a = [self.bit_to_int(bit) for bit in conns["A"]]
                b = [self.bit_to_int(bit) for bit in conns["B"]]
                y = [self.bit_to_int(bit) for bit in conns["Y"]]
                # assert len(a) == len(b) == len(y)
                self._add_aby_cell(type_, a, b, y)
            elif type_ == "$dff":
                if not self.param_to_int(params["CLK_POLARITY"]):
                    raise ValueError("$dff with negative clock polarity is not supported")
                if self._clk is None:
                    raise ValueError("Global clock is not defined")
                d, clk, q = conns["D"], conns["CLK"], conns["Q"]
                if len(clk) != 1 or self.bit_to_int(clk[0]) != self._clk:
                    raise ValueError(f"Clock {clk} does not match global clock {self._clk}")
                d = [self.bit_to_int(bit) for bit in d]
                q = [self.bit_to_int(bit) for bit in q]
                assert len(d) == len(q)
                self._add_dff(d, q)
            elif type_ == "$mux":
                a = [self.bit_to_int(bit) for bit in conns["A"]]
                b = [self.bit_to_int(bit) for bit in conns["B"]]
                s = [self.bit_to_int(bit) for bit in conns["S"]]
                y = [self.bit_to_int(bit) for bit in conns["Y"]]
                assert len(s) == 1 and len(a) == len(b) == len(y)
                self._add_absy_cell(type_, a, b, s, y)
            elif type_ in {
                "$not", "$logic_not", "$neg",
                "$reduce_and", "$reduce_or", "$reduce_bool"
            }:
                a = [self.bit_to_int(bit) for bit in conns["A"]]
                y = [self.bit_to_int(bit) for bit in conns["Y"]]
                self._add_ay_cell(type_, a, y)
            elif type_ in {
                "$eq", "$ne", "$ge", "$le", "$gt", "$lt",
                "$logic_and", "$logic_or"
            }:
                a = [self.bit_to_int(bit) for bit in conns["A"]]
                b = [self.bit_to_int(bit) for bit in conns["B"]]
                y = [self.bit_to_int(bit) for bit in conns["Y"]]
                # assert len(a) == len(b)
                self._add_aby_cell(type_, a, b, y)
            else:
                attrs = cell["attributes"]
                if "module_not_derived" in attrs and self.param_to_int(attrs["module_not_derived"]): # blackbox cell
                    self._add_blackbox_cell(name, type_, params, [(port, [self.bit_to_int(bit) for bit in signal]) for port, signal in conns.items()])
                elif type_ not in {"$scopeinfo"}:
                    raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()
        # set cnt
        self._cnt = self.execute("SELECT MAX(wire) FROM wirevec_members").fetchone()[0] or 1
        print(f"Database built with {self._cnt} wires and global clock {self._clk}")

    def _merge_cells(self) -> utils.DisjointSetUnion:
        """
        Return the wires that need to be merged.
        """
        # TODO: for now, we only check aby_cells and dffs
        dsu = utils.DisjointSetUnion()
        cur = self.execute("SELECT type, a, b, y FROM aby_cells")
        wires: dict[tuple[str, int, int], list[int]] = {}
        for type_, a, b, y in cur:
            if (type_, a, b) not in wires:
                wires[(type_, a, b)] = []
            wires[(type_, a, b)].append(y)

        for (type_, a, b), ys in wires.items():
            if len(ys) > 1:
                # remove duplicates
                # NOTE: when they have different widths, we keep the widest one
                wvs = [self._get_wirevec(y) for y in ys]
                wv0 = max(wvs, key=len)
                y0 = ys[wvs.index(wv0)]
                cur.execute("DELETE FROM aby_cells WHERE type = ? AND a = ? AND b = ? AND y != ?", (type_, a, b, y0))
                for y in ys:
                    if y == y0:
                        continue
                    wv = self._get_wirevec(y)
                    # assert len(wv0) == len(wv)
                    for w0, w in zip(wv0, wv):
                        dsu.union(w0, w)

        cur = self.execute("SELECT d, q FROM dffs")
        wires = {}
        for d, q in cur:
            if d not in wires:
                wires[d] = []
            wires[d].append(q)
        for d, qs in wires.items():
            if len(qs) > 1:
                # remove duplicates
                cur.execute("DELETE FROM dffs WHERE d = ? AND q != ?", (d, qs[0]))
                wv0 = self._get_wirevec(qs[0])
                for q in qs[1:]:
                    wv = self._get_wirevec(q)
                    assert len(wv0) == len(wv)
                    for w0, w in zip(wv0, wv):
                        dsu.union(w0, w)
        self.commit()
        return dsu

    def _merge_wires(self, wires_to_merge: utils.DisjointSetUnion):
        for w in wires_to_merge.parents:
            cur = self.execute("SELECT wirevec, idx FROM wirevec_members WHERE wire = ?", (w,))
            for wv, idx in cur.fetchall():
                cur.execute("SELECT hash FROM wirevecs WHERE id = ?", (wv,))
                old_h = cur.fetchone()[0]
                new_w = wires_to_merge.find(w)
                # update wirevec member
                cur.execute("UPDATE wirevec_members SET wire = ? WHERE wirevec = ? AND idx = ?", (new_w, wv, idx))
                # update hash
                cur.execute("UPDATE wirevecs SET hash = ? WHERE id = ?", (self._rhash.update(old_h, idx, w, new_w), wv))
        self.commit()

    def _merge_wirevecs(self):
        dsu = utils.DisjointSetUnion()
        cur = self.execute("SELECT id, hash FROM wirevecs")
        wirevecs: dict[int, list[int]] = {}
        for id, h in cur:
            if h not in wirevecs:
                wirevecs[h] = []
            wirevecs[h].append(id)

        for h, ids in wirevecs.items():
            if len(ids) > 1:
                wvs: dict[tuple[int, ...], list[int]] = {}
                for id in ids:
                    wv = self._get_wirevec(id)
                    if tuple(wv) not in wvs:
                        wvs[tuple(wv)] = []
                    wvs[tuple(wv)].append(id)
                for wvids in wvs.values():
                    if len(wvids) > 1:
                        for wvid in range(1, len(wvids)):
                            dsu.union(wvids[0], wvids[wvid])

        cur.executemany("DELETE FROM wirevecs WHERE id = ?", ((wv,) for wv in dsu.parents if dsu.find(wv) != wv))
        cur.executemany("DELETE FROM wirevec_members WHERE wirevec = ?", ((wv,) for wv in dsu.parents if dsu.find(wv) != wv))   # TODO: it seems that SQLite does not support ON DELETE CASCADE, delete manually
        self.commit()
        return dsu

    def _update_cells(self, dsu: utils.DisjointSetUnion):
        # TODO: for now, we only update aby_cells and dffs
        for wv in dsu.parents:
            leader = dsu.find(wv)
            if leader != wv:
                # update aby_cells
                cur = self.execute("SELECT type, b, y FROM aby_cells WHERE a = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM aby_cells WHERE a = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
                    ((type_, leader, b, y) for type_, b, y in rows)
                )
                cur = self.execute("SELECT type, a, y FROM aby_cells WHERE b = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM aby_cells WHERE b = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
                    ((type_, a, leader, y) for type_, a, y in rows)
                )
                cur = self.execute("SELECT type, a, b FROM aby_cells WHERE y = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM aby_cells WHERE y = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
                    ((type_, a, b, leader) for type_, a, b in rows)
                )

                # update dffs
                cur = self.execute("SELECT d, q FROM dffs WHERE d = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM dffs WHERE d = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO dffs (d, q) VALUES (?, ?)",
                    ((leader, q) for _, q in rows)
                )
                cur = self.execute("SELECT d, q FROM dffs WHERE q = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM dffs WHERE q = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO dffs (d, q) VALUES (?, ?)",
                    ((d, leader) for d, _ in rows)
                )

                # update ay_cells
                cur = self.execute("SELECT type, y FROM ay_cells WHERE a = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ay_cells WHERE a = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO ay_cells (type, a, y) VALUES (?, ?, ?)",
                    ((type_, leader, y) for type_, y in rows)
                )
                cur = self.execute("SELECT type, a FROM ay_cells WHERE y = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ay_cells WHERE y = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO ay_cells (type, a, y) VALUES (?, ?, ?)",
                    ((type_, a, leader) for type_, a in rows)
                )

                # update absy_cells
                cur = self.execute("SELECT type, b, s, y FROM absy_cells WHERE a = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM absy_cells WHERE a = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, leader, b, s, y) for type_, b, s, y in rows)
                )
                cur = self.execute("SELECT type, a, s, y FROM absy_cells WHERE b = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM absy_cells WHERE b = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, a, leader, s, y) for type_, a, s, y in rows)
                )
                cur = self.execute("SELECT type, a, b, y FROM absy_cells WHERE s = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM absy_cells WHERE s = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, a, b, leader, y) for type_, a, b, y in rows)
                )
                cur = self.execute("SELECT type, a, b, s FROM absy_cells WHERE y = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM absy_cells WHERE y = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO absy_cells (type, a, b, s, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, a, b, s, leader) for type_, a, b, s in rows)
                )

                # update from_inputs
                self.execute("UPDATE from_inputs SET source = ? WHERE source = ?", (leader, wv))
                # update as_outputs
                self.execute("UPDATE as_outputs SET sink = ? WHERE sink = ?", (leader, wv))
                # TODO: update instance_ports
        self.commit()

    def rebuild_once(self) -> bool:
        # union
        # merge_cells -> merge_wires -> merge_wirevecs -> update_cells
        # all phases are batched processing
        # TODO: parallelize them
        wires_to_merge = self._merge_cells()
        if not wires_to_merge.parents:
            return False
        self._merge_wires(wires_to_merge)
        wirevecs_to_merge = self._merge_wirevecs()
        self._update_cells(wirevecs_to_merge)
        return True

    def rebuild(self) -> int:
        cnt = 0
        while self.rebuild_once():
            cnt += 1
        return cnt