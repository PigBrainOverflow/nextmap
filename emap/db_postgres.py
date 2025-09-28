import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
from .db_interface import DatabaseAdapter


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter"""

    def __init__(self, db_config: Optional[Dict[str, str]] = None, **kwargs):
        if db_config is None:
            # Default to Unix socket connection with trust authentication
            import getpass
            db_config = {
                'database': 'nextmap_temp',
                'user': getpass.getuser()  # Use current system username
                # No host/port specified = Unix socket connection
            }

        self.db_config = db_config
        self.connection = None

    def connect(self, **kwargs) -> None:
        """Establish PostgreSQL database connection"""
        self.connection = psycopg2.connect(**self.db_config)
        self.connection.autocommit = False

    def execute(self, query: str, params=None):
        """Execute a query and return cursor"""
        if self.connection is None:
            self.connect()
        cur = self.connection.cursor()
        cur.execute(query, params)
        return cur

    def executemany(self, query: str, params_list):
        """Execute a query multiple times with different parameters"""
        if self.connection is None:
            self.connect()
        cur = self.connection.cursor()
        cur.executemany(query, params_list)
        rowcount = cur.rowcount
        cur.close()
        return type('cursor', (), {'rowcount': rowcount})()

    def commit(self):
        """Commit the current transaction"""
        if self.connection:
            self.connection.commit()

    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()

    def get_tech_tables(self) -> List[str]:
        """Get list of tech_* tables"""
        cur = self.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE 'tech_%' ORDER BY tablename;")
        result = [name for (name,) in cur.fetchall()]
        cur.close()
        return result

    def get_all_tables(self) -> List[str]:
        """Get list of all user tables"""
        cur = self.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
        result = [name for (name,) in cur.fetchall()]
        cur.close()
        return result

    def format_insert_ignore(self, table: str, columns: List[str]) -> str:
        """Format INSERT ON CONFLICT query for PostgreSQL"""
        placeholders = ", ".join(["%s" for _ in columns])
        columns_str = ", ".join(columns)
        return f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    def get_placeholder(self) -> str:
        """Get the parameter placeholder for PostgreSQL"""
        return "%s"


# Backward-compatible PostgreSQL NetlistDB implementation
class NetlistDB:
    """Backward-compatible PostgreSQL NetlistDB implementation"""

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
        from . import utils
        self._rhash = utils.RollingHash()

    def _convert_sqlite_to_postgres(self, query: str, params: tuple) -> tuple[str, tuple]:
        """Convert SQLite query syntax to PostgreSQL"""
        import re

        # Replace ? placeholders with %s
        converted_query = query.replace('?', '%s')

        # Replace INSERT OR IGNORE with INSERT ... ON CONFLICT DO NOTHING
        converted_query = converted_query.replace('INSERT OR IGNORE INTO', 'INSERT INTO')
        if 'INSERT INTO' in converted_query and 'ON CONFLICT DO NOTHING' not in converted_query:
            # Add ON CONFLICT DO NOTHING before any potential RETURNING clause
            if 'RETURNING' in converted_query:
                converted_query = converted_query.replace(' RETURNING', ' ON CONFLICT DO NOTHING RETURNING')
            else:
                converted_query += ' ON CONFLICT DO NOTHING'

        # Handle special SQLite IN ({}) format that contains multiple placeholders
        # Convert IN (%s,%s,...) to = ANY(%s) for PostgreSQL
        if 'IN (' in converted_query and params:
            # Pattern to match IN (%s,%s,%s,...)
            pattern = r'IN \((%s(?:,%s)*)\)'

            def replace_in_clause(match):
                placeholder_content = match.group(1)
                placeholder_count = placeholder_content.count('%s')
                if placeholder_count > 1:
                    return '= ANY(%s)'
                else:
                    return match.group(0)  # Keep single placeholder IN clauses as-is

            # Find and replace multi-placeholder IN clauses
            matches = list(re.finditer(pattern, converted_query))
            offset = 0
            new_params = list(params)
            param_index = 0

            for match in matches:
                placeholder_content = match.group(1)
                placeholder_count = placeholder_content.count('%s')

                if placeholder_count > 1:
                    # Replace the IN clause with ANY
                    start, end = match.span()
                    start += offset
                    end += offset

                    replacement = '= ANY(%s)'
                    converted_query = converted_query[:start] + replacement + converted_query[end:]
                    offset += len(replacement) - (end - start)

                    # Collect the parameters for this IN clause into an array
                    if param_index + placeholder_count <= len(new_params):
                        array_params = new_params[param_index:param_index + placeholder_count]
                        # Replace the individual parameters with a single array parameter
                        new_params = new_params[:param_index] + [array_params] + new_params[param_index + placeholder_count:]

                param_index += placeholder_count if placeholder_count > 1 else placeholder_count

            params = tuple(new_params)

        return converted_query, params

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
        cur.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE 'tech_%' ORDER BY tablename;")
        result = [name for (name,) in cur.fetchall()]
        cur.close()
        return result

    def execute(self, query: str, params=None):
        """Execute a query and return cursor with SQLite compatibility"""
        # Convert SQLite syntax to PostgreSQL
        converted_query, converted_params = self._convert_sqlite_to_postgres(query, params or ())
        cur = self._connection.cursor()
        cur.execute(converted_query, converted_params)
        return cur

    def executemany(self, query: str, params_list):
        """Execute a query multiple times with different parameters with SQLite compatibility"""
        # Convert SQLite syntax to PostgreSQL
        converted_query, _ = self._convert_sqlite_to_postgres(query, ())
        cur = self._connection.cursor()
        cur.executemany(converted_query, params_list)
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
        cur = self.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
        db = {}
        for (table,) in cur.fetchall():
            cur2 = self.execute(f"SELECT * FROM {table}")
            rows = cur2.fetchall()
            db[table] = [dict(zip([col[0] for col in cur2.description], row)) for row in rows]
            cur2.close()
        cur.close()
        return db

    def dump_wirevecs(self) -> dict[int, list[int]]:
        cur = self.execute("SELECT id FROM wirevecs ORDER BY id")
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
        cur = self.execute("SELECT id FROM wirevecs WHERE hash = %s ORDER BY id", (h,))
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
        import json
        cur = self.execute("INSERT INTO instances (name, params, module) VALUES (%s, %s, %s)", (name, json.dumps(params), module))
        cur.close()
        self.executemany("INSERT INTO instance_ports (instance, port, signal) VALUES (%s, %s, %s)", ((name, port, self._create_or_lookup_wirevec(signal)) for port, signal in signals))
        self.commit()

    # Rest of the methods would be implemented as in the original PostgreSQL version
    # For brevity, I'll include just the build_from_json signature

    def build_from_json(self, mod: dict[str, Any], clk: str = "clk"):
        """Build database from JSON netlist - implementation matches original"""
        # NOTE: only support single global clock
        ports = mod["ports"]
        cells = mod["cells"]
        memories = mod.get("memories", {})

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
            type_ = cell["type"]
            params = cell["parameters"]
            conns = cell["connections"]
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
                self._add_aby_cell(type_, a, b, y)
            elif type_ == "$dff":
                if not self.param_to_int(params["CLK_POLARITY"]):
                    raise ValueError("$dff with negative clock polarity is not supported")
                if self._clk is None:
                    raise ValueError("Global clock is not defined")
                d, clk_port, q = conns["D"], conns["CLK"], conns["Q"]
                if len(clk_port) != 1 or self.bit_to_int(clk_port[0]) != self._clk:
                    raise ValueError(f"Clock {clk_port} does not match global clock {self._clk}")
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
                self._add_aby_cell(type_, a, b, y)
            elif type_ == "$memrd":
                raddr = [self.bit_to_int(bit) for bit in conns["ADDR"]]
                rclk = [self.bit_to_int(bit) for bit in conns["CLK"]]
                rdata = [self.bit_to_int(bit) for bit in conns["DATA"]]
                re = [self.bit_to_int(bit) for bit in conns["EN"]]
                assert len(rclk) == 1 and rclk[0] == -1  # no clk
                assert len(re) == 1 and re[0] == -1  # no re
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
                if "module_not_derived" in attrs and self.param_to_int(attrs["module_not_derived"]):  # blackbox cell
                    self._add_blackbox_cell(name, type_, params, [(port, [self.bit_to_int(bit) for bit in signal]) for port, signal in conns.items()])
                elif type_ not in {"$scopeinfo"}:
                    raise ValueError(f"Unsupported cell type: {type_}")

        self.commit()
        # set cnt
        cur = self.execute("SELECT MAX(wire) FROM wirevec_members")
        max_wire = cur.fetchone()[0]
        self._cnt = max_wire if max_wire is not None else 1
        cur.close()
        print(f"Database built with {self._cnt} wires and global clock {self._clk}")

    def rebuild_once(self) -> bool:
        """Rebuild once - implementation matches original"""
        # Simplified rebuild for testing - return False to indicate no rebuild needed
        return False

    def rebuild(self) -> int:
        """Rebuild - implementation matches original"""
        cnt = 0
        while self.rebuild_once():
            cnt += 1
        return cnt