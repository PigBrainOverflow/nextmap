import psycopg2
import psycopg2.extras
import json
from typing import Any
from . import utils


class NetlistDB:
    _connection: psycopg2.extensions.connection
    _db_config: dict[str, str]
    _clk: int | None
    _cnt: int
    _rhash: utils.RollingHash

    @staticmethod
    def bit_to_int(bit: str | int) -> int:
        return -1 if bit == "x" else int(bit)

    @staticmethod
    def param_to_int(param: str | int) -> int:
        return param if isinstance(param, int) else int(param, base=2)

    def width_of(self, id) -> int:
        cur = self._connection.cursor()
        cur.execute("SELECT MAX(idx) FROM wirevec_members WHERE wirevec = %s", (id,))
        result = cur.fetchone()
        cur.close()
        return result[0] + 1

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
        cur = self._connection.cursor()
        cur.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE 'tech_%';")
        result = [name for (name,) in cur.fetchall()]
        cur.close()
        return result

    def __init__(self, schema_file: str, db_config: dict[str, str] = None, cnt: int = 0):
        if db_config is None:
            # Default to Unix socket connection with trust authentication
            import getpass
            db_config = {
                'database': 'nextmap_temp',
                'user': getpass.getuser()  # Use current system username
                # No host/port specified = Unix socket connection
            }

        self._db_config = db_config
        self._connection = psycopg2.connect(**db_config)
        self._connection.autocommit = False

        with open(schema_file, "r") as f:
            cur = self._connection.cursor()
            cur.execute(f.read())
            cur.close()
            self._connection.commit()

        self._clk = None
        self._cnt = cnt
        self._rhash = utils.RollingHash()

    def execute(self, query: str, params=None):
        """Execute a query and return cursor"""
        cur = self._connection.cursor()
        cur.execute(query, params)
        return cur

    def executemany(self, query: str, params_list):
        """Execute a query multiple times with different parameters"""
        cur = self._connection.cursor()
        cur.executemany(query, params_list)
        rowcount = cur.rowcount
        cur.close()
        return type('cursor', (), {'rowcount': rowcount})()

    def commit(self):
        """Commit the current transaction"""
        self._connection.commit()

    def close(self):
        """Close the database connection"""
        self._connection.close()

    def dump_tables(self) -> dict:
        # get all tables except postgres internal tables
        cur = self.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        db = {}
        for (table,) in cur.fetchall():
            cur2 = self.execute(f"SELECT * FROM {table}")
            rows = cur2.fetchall()
            db[table] = [dict(zip([col[0] for col in cur2.description], row)) for row in rows]
            cur2.close()
        cur.close()
        return db

    def dump_wirevecs(self) -> dict[int, list[int]]:
        cur = self.execute("SELECT id FROM wirevecs")
        wvs = {}
        for (id,) in cur.fetchall():
            wvs[id] = self._get_wirevec(id)
        return wvs

    def _get_wirevec(self, id: int) -> list[int]:
        cur = self.execute("SELECT wire FROM wirevec_members WHERE wirevec = %s ORDER BY idx", (id,))
        result = [w for (w,) in cur.fetchall()]
        cur.close()
        return result

    def _add_wirevec(self, wv: list[int]) -> int:
        h = self._rhash.hash(wv)
        cur = self.execute("INSERT INTO wirevecs (hash) VALUES (%s) RETURNING id", (h,))
        id = cur.fetchone()[0]
        cur.close()
        self.executemany(
            "INSERT INTO wirevec_members (wirevec, idx, wire) VALUES (%s, %s, %s)",
            ((id, i, w) for i, w in enumerate(wv))
        )
        self.commit()
        return id

    def _create_or_lookup_wirevec(self, wv: list[int]) -> int:
        h = self._rhash.hash(wv)
        cur = self.execute("SELECT id FROM wirevecs WHERE hash = %s", (h,))
        rows = cur.fetchall()
        cur.close()
        for (id,) in rows:  # lookup
            if self._get_wirevec(id) == wv:
                return id
        # not found, insert
        cur = self.execute("INSERT INTO wirevecs (hash) VALUES (%s) RETURNING id", (h,))
        id = cur.fetchone()[0]
        cur.close()
        self.executemany(
            "INSERT INTO wirevec_members (wirevec, idx, wire) VALUES (%s, %s, %s)",
            ((id, i, w) for i, w in enumerate(wv))
        )
        self.commit()
        return id

    def _add_input(self, name: str, source: list[int]):
        ws = self._create_or_lookup_wirevec(source)
        cur = self.execute("INSERT INTO from_inputs (source, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", (ws, name))
        cur.close()
        self.commit()

    def _add_output(self, name: str, sink: list[int]):
        ws = self._create_or_lookup_wirevec(sink)
        cur = self.execute("INSERT INTO as_outputs (sink, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", (ws, name))
        cur.close()
        self.commit()

    def _add_dff(self, d: list[int], q: list[int]):
        wvd = self._create_or_lookup_wirevec(d)
        wvq = self._create_or_lookup_wirevec(q)
        cur = self.execute("INSERT INTO dffs (d, q) VALUES (%s, %s) ON CONFLICT DO NOTHING", (wvd, wvq))
        cur.close()
        self.commit()

    def _add_ay_cell(self, type_: str, a: list[int], y: list[int]):
        wva, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(y)
        cur = self.execute("INSERT INTO ay_cells (type, a, y) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (type_, wva, wvy))
        cur.close()
        self.commit()

    def _add_aby_cell(self, type_: str, a: list[int], b: list[int], y: list[int]):
        wva, wvb, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(b), self._create_or_lookup_wirevec(y)
        cur = self.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (type_, wva, wvb, wvy))
        cur.close()
        self.commit()

    def _add_absy_cell(self, type_: str, a: list[int], b: list[int], s: list[int], y: list[int]):
        wva, wvb, wvs, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(b), self._create_or_lookup_wirevec(s), self._create_or_lookup_wirevec(y)
        cur = self.execute("INSERT INTO absy_cells (type, a, b, s, y) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (type_, wva, wvb, wvs, wvy))
        cur.close()
        self.commit()

    def _add_blackbox_cell(self, name: str, module: str, params: dict[str, Any], signals: list[tuple[str, list[int]]]):
        cur = self.execute("INSERT INTO instances (name, params, module) VALUES (%s, %s, %s)", (name, json.dumps(params), module))
        cur.close()
        self.executemany("INSERT INTO instance_ports (instance, port, signal) VALUES (%s, %s, %s)", ((name, port, self._create_or_lookup_wirevec(signal)) for port, signal in signals))
        self.commit()

    def build_from_json_cpp(self, mod: dict[str, Any], clk: str = "clk"):
        # PostgreSQL doesn't have in-memory databases like SQLite, so we check the database name instead
        if self._db_config.get('database') == 'nextmap_temp':
            raise RuntimeError("Cannot call build_from_json_cpp() on temporary database")
        try:
            from .emapcc.build import emapcc
            # Note: emapcc might need to be updated to work with PostgreSQL connection info
            db_file_equivalent = f"postgresql://{self._db_config.get('user')}@{self._db_config.get('host')}:{self._db_config.get('port')}/{self._db_config.get('database')}"
            self._clk, self._cnt = emapcc.build_from_json(db_file_equivalent, mod, clk, self._rhash._POWER_B[1], self._rhash._M)
        except ImportError:
            raise RuntimeError("Module emapcc is not available. Please build emapcc to use build_from_json_cpp()")
        except Exception as e:
            raise RuntimeError(f"Failed to build from JSON: {e}")

    def build_from_json(self, mod: dict[str, Any], clk: str = "clk"):
        # NOTE: only support single global clock
        ports: dict[str, Any] = mod["ports"]
        cells: dict[str, Any] = mod["cells"]
        memories: dict[str, Any] = mod.get("memories", {})

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

        # build memories
        for name, mem in memories.items():
            cur = self.execute("INSERT INTO memories (name, width, size) VALUES (%s, %s, %s)", (name, mem["width"], mem["size"]))
            cur.close()

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
            elif type_ == "$memrd":
                raddr = [self.bit_to_int(bit) for bit in conns["ADDR"]]
                rclk = [self.bit_to_int(bit) for bit in conns["CLK"]]
                rdata = [self.bit_to_int(bit) for bit in conns["DATA"]]
                re = [self.bit_to_int(bit) for bit in conns["EN"]]
                assert len(rclk) == 1 and rclk[0] == -1 # no clk
                assert len(re) == 1 and re[0] == -1 # no re
                cur = self.execute("INSERT INTO memrds (memory, raddr, rdata) VALUES (%s, %s, %s)", (params["MEMID"][1:], self._create_or_lookup_wirevec(raddr), self._create_or_lookup_wirevec(rdata)))
                cur.close()
            elif type_ == "$memwr_v2":
                waddr = [self.bit_to_int(bit) for bit in conns["ADDR"]]
                wclk = [self.bit_to_int(bit) for bit in conns["CLK"]]
                wdata = [self.bit_to_int(bit) for bit in conns["DATA"]]
                we = [self.bit_to_int(bit) for bit in conns["EN"]]
                assert len(wclk) == 1 and wclk[0] == self._clk
                cur = self.execute("INSERT INTO memwrs (memory, waddr, wdata, we) VALUES (%s, %s, %s, %s)", (params["MEMID"][1:], self._create_or_lookup_wirevec(waddr), self._create_or_lookup_wirevec(wdata), self._create_or_lookup_wirevec(we)))
                cur.close()
            else:
                attrs = cell["attributes"]
                if "module_not_derived" in attrs and self.param_to_int(attrs["module_not_derived"]): # blackbox cell
                    self._add_blackbox_cell(name, type_, params, [(port, [self.bit_to_int(bit) for bit in signal]) for port, signal in conns.items()])
                elif type_ not in {"$scopeinfo"}:
                    raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()
        # set cnt
        cur = self.execute("SELECT MAX(wire) FROM wirevec_members")
        self._cnt = cur.fetchone()[0] or 1
        cur.close()
        print(f"Database built with {self._cnt} wires and global clock {self._clk}")

    def _merge_cells(self) -> utils.DisjointSetUnion:
        """
        Return the wires that need to be merged.
        """
        # TODO: for now, we only check aby_cells and dffs
        dsu = utils.DisjointSetUnion()
        cur = self.execute("SELECT type, a, b, y FROM aby_cells")
        wires: dict[tuple[str, int, int], list[int]] = {}
        for type_, a, b, y in cur.fetchall():
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
                cur2 = self.execute("DELETE FROM aby_cells WHERE type = %s AND a = %s AND b = %s AND y != %s", (type_, a, b, y0))
                cur2.close()
                for y in ys:
                    if y == y0:
                        continue
                    wv = self._get_wirevec(y)
                    # assert len(wv0) == len(wv)
                    for w0, w in zip(wv0, wv):
                        dsu.union(w0, w)
        cur.close()

        cur = self.execute("SELECT d, q FROM dffs")
        wires = {}
        for d, q in cur:
            if d not in wires:
                wires[d] = []
            wires[d].append(q)
        for d, qs in wires.items():
            if len(qs) > 1:
                # remove duplicates
                cur2 = self.execute("DELETE FROM dffs WHERE d = %s AND q != %s", (d, qs[0]))
                cur2.close()
                wv0 = self._get_wirevec(qs[0])
                for q in qs[1:]:
                    wv = self._get_wirevec(q)
                    assert len(wv0) == len(wv)
                    for w0, w in zip(wv0, wv):
                        dsu.union(w0, w)
        cur.close()
        self.commit()
        return dsu

    def _merge_wires(self, wires_to_merge: utils.DisjointSetUnion):
        for w in wires_to_merge.parents:
            cur = self.execute("SELECT wirevec, idx FROM wirevec_members WHERE wire = %s", (w,))
            for wv, idx in cur.fetchall():
                cur2 = self.execute("SELECT hash FROM wirevecs WHERE id = %s", (wv,))
                old_h = cur2.fetchone()[0]
                cur2.close()
                new_w = wires_to_merge.find(w)
                # update wirevec member
                cur3 = self.execute("UPDATE wirevec_members SET wire = %s WHERE wirevec = %s AND idx = %s", (new_w, wv, idx))
                cur3.close()
                # update hash
                cur4 = self.execute("UPDATE wirevecs SET hash = %s WHERE id = %s", (self._rhash.update(old_h, idx, w, new_w), wv))
                cur4.close()
            cur.close()
        self.commit()

    def _merge_wirevecs(self):
        dsu = utils.DisjointSetUnion()
        cur = self.execute("SELECT id, hash FROM wirevecs")
        wirevecs: dict[int, list[int]] = {}
        for id, h in cur.fetchall():
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
        cur.close()

        cur2 = self._connection.cursor()
        cur2.executemany("DELETE FROM wirevecs WHERE id = %s", ((wv,) for wv in dsu.parents if dsu.find(wv) != wv))
        cur2.close()
        cur3 = self._connection.cursor()
        cur3.executemany("DELETE FROM wirevec_members WHERE wirevec = %s", ((wv,) for wv in dsu.parents if dsu.find(wv) != wv))   # TODO: it seems that PostgreSQL supports ON DELETE CASCADE, but delete manually for compatibility
        cur3.close()
        self.commit()
        return dsu

    def _update_cells(self, dsu: utils.DisjointSetUnion):
        # TODO: for now, we only update aby_cells and dffs
        for wv in dsu.parents:
            leader = dsu.find(wv)
            if leader != wv:
                # update aby_cells
                cur = self.execute("SELECT type, b, y FROM aby_cells WHERE a = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM aby_cells WHERE a = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, leader, b, y) for type_, b, y in rows)
                )
                cur.close()
                cur = self.execute("SELECT type, a, y FROM aby_cells WHERE b = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM aby_cells WHERE b = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, a, leader, y) for type_, a, y in rows)
                )
                cur.close()
                cur = self.execute("SELECT type, a, b FROM aby_cells WHERE y = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM aby_cells WHERE y = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, a, b, leader) for type_, a, b in rows)
                )
                cur.close()

                # update dffs
                cur = self.execute("SELECT d, q FROM dffs WHERE d = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM dffs WHERE d = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO dffs (d, q) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    ((leader, q) for _, q in rows)
                )
                cur.close()
                cur = self.execute("SELECT d, q FROM dffs WHERE q = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM dffs WHERE q = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO dffs (d, q) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    ((d, leader) for d, _ in rows)
                )
                cur.close()

                # update ay_cells
                cur = self.execute("SELECT type, y FROM ay_cells WHERE a = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM ay_cells WHERE a = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO ay_cells (type, a, y) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, leader, y) for type_, y in rows)
                )
                cur.close()
                cur = self.execute("SELECT type, a FROM ay_cells WHERE y = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM ay_cells WHERE y = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO ay_cells (type, a, y) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, a, leader) for type_, a in rows)
                )
                cur.close()

                # update absy_cells
                cur = self.execute("SELECT type, b, s, y FROM absy_cells WHERE a = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM absy_cells WHERE a = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO absy_cells (type, a, b, s, y) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, leader, b, s, y) for type_, b, s, y in rows)
                )
                cur.close()
                cur = self.execute("SELECT type, a, s, y FROM absy_cells WHERE b = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM absy_cells WHERE b = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO absy_cells (type, a, b, s, y) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, a, leader, s, y) for type_, a, s, y in rows)
                )
                cur.close()
                cur = self.execute("SELECT type, a, b, y FROM absy_cells WHERE s = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM absy_cells WHERE s = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO absy_cells (type, a, b, s, y) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, a, b, leader, y) for type_, a, b, y in rows)
                )
                cur.close()
                cur = self.execute("SELECT type, a, b, s FROM absy_cells WHERE y = %s", (wv,))
                rows = cur.fetchall()
                cur.close()
                cur = self.execute("DELETE FROM absy_cells WHERE y = %s", (wv,))
                cur.close()
                cur = self._connection.cursor()
                cur.executemany(
                    "INSERT INTO absy_cells (type, a, b, s, y) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ((type_, a, b, s, leader) for type_, a, b, s in rows)
                )
                cur.close()

                # update from_inputs
                cur = self.execute("UPDATE from_inputs SET source = %s WHERE source = %s", (leader, wv))
                cur.close()
                # update as_outputs
                cur = self.execute("UPDATE as_outputs SET sink = %s WHERE sink = %s", (leader, wv))
                cur.close()
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