import sqlite3
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

    @staticmethod
    def param_to_int(param: str | int) -> int:
        return param if isinstance(param, int) else int(param, base=2)

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

        # build consts
        # self._add_input("VCC", [1]) # VCC is always 1
        # self._add_input("GND", [0]) # GND is always 0
        # self._add_input("DC", [-1]) # DC is always x

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

            # NOTE: We may not need arithmetic cells
            # arith_aby_cells
            elif type_ in {"$add", "$sub", "$mul"}:
                type_ += "s" if self.param_to_int(params["A_SIGNED"]) and self.param_to_int(params["B_SIGNED"]) else "u"
                awv = [self.bit_to_int(bit) for bit in conns["A"]]
                bwv = [self.bit_to_int(bit) for bit in conns["B"]]
                ywv = [self.bit_to_int(bit) for bit in conns["Y"]]
                self.execute("INSERT INTO arith_aby_cells (type, a, b, y_width, y) VALUES (?, ?, ?, ?, ?)", (type_, self._create_or_lookup_wirevec(awv), self._create_or_lookup_wirevec(bwv), len(ywv), self._create_or_lookup_wirevec(ywv)))
            else:
                raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()

    # Rebuild-related methods
    def _merge_cells(self, dsu: utils.DisjointSetUnion):
        # deduplicate ay_cells
        cur = self.execute("SELECT type, a, y FROM ay_cells")
        ay_cells_pk: dict[tuple[str, int], list[int]] = {}
        for type_, a, y in cur:
            if (type_, a) not in ay_cells_pk:
                ay_cells_pk[(type_, a)] = []
            ay_cells_pk[(type_, a)].append(y)
        for (type_, a), ys in ay_cells_pk.items():
            if len(ys) > 1:
                # remove duplicates
                # we keep ys[0]
                cur.execute("DELETE FROM ay_cells WHERE type = ? AND a = ? AND y != ?", (type_, a, ys[0]))
                for y in ys[1:]:
                    dsu.union(ys[0], y)
        self.commit()

        # deduplicate aby_cells
        cur = self.execute("SELECT type, a, b, y FROM aby_cells")
        aby_cells_pk: dict[tuple[str, int, int], list[int]] = {}
        for type_, a, b, y in cur:
            if (type_, a, b) not in aby_cells_pk:
                aby_cells_pk[(type_, a, b)] = []
            aby_cells_pk[(type_, a, b)].append(y)
        for (type_, a, b), ys in aby_cells_pk.items():
            if len(ys) > 1:
                # remove duplicates
                # we keep ys[0]
                cur.execute("DELETE FROM aby_cells WHERE type = ? AND a = ? AND b = ? AND y != ?", (type_, a, b, ys[0]))
                for y in ys[1:]:
                    dsu.union(ys[0], y)
        self.commit()

        # deduplicate muxes
        cur = self.execute("SELECT a, b, s, y FROM muxes")
        muxes_pk: dict[tuple[int, int, int], list[int]] = {}
        for a, b, s, y in cur:
            if (a, b, s) not in muxes_pk:
                muxes_pk[(a, b, s)] = []
            muxes_pk[(a, b, s)].append(y)
        for (a, b, s), ys in muxes_pk.items():
            if len(ys) > 1:
                # remove duplicates
                # we keep ys[0]
                cur.execute("DELETE FROM muxes WHERE a = ? AND b = ? AND s = ? AND y != ?", (a, b, s, ys[0]))
                for y in ys[1:]:
                    dsu.union(ys[0], y)
        self.commit()

        # deduplicate arith_aby_cells
        cur = self.execute("SELECT type, a, b, y_width, y FROM arith_aby_cells")
        arith_aby_cells_pk: dict[tuple[str, int, int, int], list[int]] = {}
        for type_, a, b, y_width in cur:
            if (type_, a, b, y_width) not in arith_aby_cells_pk:
                arith_aby_cells_pk[(type_, a, b, y_width)] = []
            arith_aby_cells_pk[(type_, a, b, y_width)].append(y)

        for (type_, a, b, y_width), ys in arith_aby_cells_pk.items():
            if len(ys) > 1:
                # union of wirevecs
                # remove duplicates
                # we keep wvs[0]
                wvs = [self._get_wirevec(y) for y in ys]
                cur.execute("DELETE FROM arith_aby_cells WHERE type = ? AND a = ? AND b = ? AND y_width = ? AND y != ?", (type_, a, b, y_width, ys[0]))
                for wv in wvs[1:]:
                    for (w0, w) in zip(wvs[0], wv):
                        dsu.union(w0, w)
        self.commit()

    def _merge_wires(self, wires_to_merge: utils.DisjointSetUnion):
        # propagate wire updates to wirevecs
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

    def _merge_wirevecs(self) -> utils.DisjointSetUnion:
        # deduplicate wirevecs
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
        cur.executemany("DELETE FROM wirevec_members WHERE wirevec = ?", ((wv,) for wv in dsu.parents if dsu.find(wv) != wv))   # NOTE: it seems that SQLite does not support ON DELETE CASCADE, delete manually
        self.commit()
        return dsu

    def _update_cells(self, wdsu: utils.DisjointSetUnion, wvdsu: utils.DisjointSetUnion):
        # propagate wire updates to cells
        for i, w in enumerate(wdsu.parents):
            if i % 1000 == 0:
                print(f"Updating cells for wire {i}/{len(wdsu.parents)}")
            leader = wdsu.find(w)
            if leader != w:
                # update ay_cells
                cur = self.execute("SELECT type, y FROM ay_cells WHERE a = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ay_cells WHERE a = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO ay_cells (type, a, y) VALUES (?, ?, ?)",
                    ((type_, leader, y) for type_, y in rows)
                )
                cur = self.execute("SELECT type, a FROM ay_cells WHERE y = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM ay_cells WHERE y = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO ay_cells (type, a, y) VALUES (?, ?, ?)",
                    ((type_, a, leader) for type_, a in rows)
                )

                # update aby_cells
                cur = self.execute("SELECT type, b, y FROM aby_cells WHERE a = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM aby_cells WHERE a = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
                    ((type_, leader, b, y) for type_, b, y in rows)
                )
                cur = self.execute("SELECT type, a, y FROM aby_cells WHERE b = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM aby_cells WHERE b = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
                    ((type_, a, leader, y) for type_, a, y in rows)
                )
                cur = self.execute("SELECT type, a, b FROM aby_cells WHERE y = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM aby_cells WHERE y = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
                    ((type_, a, b, leader) for type_, a, b in rows)
                )

                # update muxes
                cur = self.execute("SELECT b, s, y FROM muxes WHERE a = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM muxes WHERE a = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO muxes (a, b, s, y) VALUES (?, ?, ?, ?)",
                    ((leader, b, s, y) for b, s, y in rows)
                )
                cur = self.execute("SELECT a, s, y FROM muxes WHERE b = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM muxes WHERE b = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO muxes (a, b, s, y) VALUES (?, ?, ?, ?)",
                    ((a, leader, s, y) for a, s, y in rows)
                )
                cur = self.execute("SELECT a, b, s FROM muxes WHERE y = ?", (w,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM muxes WHERE y = ?", (w,))
                cur.executemany(
                    "INSERT OR IGNORE INTO muxes (a, b, s, y) VALUES (?, ?, ?, ?)",
                    ((a, b, s, leader) for a, b, s in rows)
                )

        # propagate wirevec updates to wires
        for i, wv in enumerate(wvdsu.parents):
            if i % 1000 == 0:
                print(f"Updating arith_aby_cells for wirevec {i}/{len(wvdsu.parents)}")
            leader = wvdsu.find(wv)
            if leader != wv:
                # update arith_aby_cells
                cur = self.execute("SELECT type, b, y_width, y FROM arith_aby_cells WHERE a = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM arith_aby_cells WHERE a = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO arith_aby_cells (type, a, b, y_width, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, leader, b, y_width, y) for type_, b, y_width, y in rows)
                )
                cur = self.execute("SELECT type, a, y_width, y FROM arith_aby_cells WHERE b = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM arith_aby_cells WHERE b = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO arith_aby_cells (type, a, b, y_width, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, a, leader, y_width, y) for type_, a, y_width, y in rows)
                )
                cur = self.execute("SELECT type, a, b, y_width FROM arith_aby_cells WHERE y = ?", (wv,))
                rows = cur.fetchall()
                cur.execute("DELETE FROM arith_aby_cells WHERE y = ?", (wv,))
                cur.executemany(
                    "INSERT OR IGNORE INTO arith_aby_cells (type, a, b, y_width, y) VALUES (?, ?, ?, ?, ?)",
                    ((type_, a, b, y_width, leader) for type_, a, b, y_width in rows)
                )

                # update from_inputs
                self.execute("UPDATE from_inputs SET source = ? WHERE source = ?", (leader, wv))
                # update as_outputs
                self.execute("UPDATE as_outputs SET sink = ? WHERE sink = ?", (leader, wv))
        self.commit()

    def rebuild_once(self, wdsu: utils.DisjointSetUnion) -> bool:
        # merge_cells -> merge_wires -> merge_wirevecs -> update_cells
        # all phases are batched processing
        print("Rebuilding...")
        self._merge_cells(wdsu)
        if not wdsu.parents:
            return False
        self._merge_wires(wdsu)
        wvdsu = self._merge_wirevecs()
        self._update_cells(wdsu, wvdsu)
        return True

    def rebuild(self, wdsu: utils.DisjointSetUnion) -> int:
        cnt = 0
        while self.rebuild_once(wdsu):
            cnt += 1
            wdsu.parents.clear()    # clear the worklist
        return cnt