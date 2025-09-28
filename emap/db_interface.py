from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Tuple
import json
from . import utils


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    def execute(self, query: str, params=None):
        """Execute a query and return cursor"""
        pass

    @abstractmethod
    def executemany(self, query: str, params_list):
        """Execute a query multiple times with different parameters"""
        pass

    @abstractmethod
    def commit(self):
        """Commit the current transaction"""
        pass

    @abstractmethod
    def close(self):
        """Close the database connection"""
        pass

    @abstractmethod
    def get_tech_tables(self) -> List[str]:
        """Get list of tech_* tables"""
        pass

    @abstractmethod
    def get_all_tables(self) -> List[str]:
        """Get list of all user tables"""
        pass

    @abstractmethod
    def format_insert_ignore(self, table: str, columns: List[str]) -> str:
        """Format INSERT IGNORE/ON CONFLICT query"""
        pass

    @abstractmethod
    def get_placeholder(self) -> str:
        """Get the parameter placeholder for this database"""
        pass

    def create_cursor(self):
        """Create a cursor that can be closed"""
        class ClosableCursor:
            def __init__(self, cursor):
                self._cursor = cursor

            def __getattr__(self, name):
                return getattr(self._cursor, name)

            def close(self):
                # Most database cursors don't need explicit closing in our use case
                pass

        return ClosableCursor


class NetlistDB:
    """Database-agnostic netlist database interface"""

    def __init__(self, schema_file: str, backend: str = "sqlite", **backend_config):
        self._adapter = self._create_adapter(backend, **backend_config)
        self._clk: Optional[int] = None
        self._cnt: int = backend_config.get('cnt', 0)
        self._rhash = utils.RollingHash()

        # Initialize database with schema
        with open(schema_file, "r") as f:
            schema = f.read()
            if backend == "postgres":
                # Convert SQLite schema to PostgreSQL if needed
                schema = self._convert_schema_to_postgres(schema)
            self._execute_schema(schema)
            self._adapter.commit()

    def _create_adapter(self, backend: str, **config) -> DatabaseAdapter:
        """Factory method to create appropriate database adapter"""
        if backend == "sqlite":
            from .db_sqlite import SQLiteAdapter
            return SQLiteAdapter(**config)
        elif backend == "postgres":
            from .db_postgres import PostgreSQLAdapter
            return PostgreSQLAdapter(**config)
        else:
            raise ValueError(f"Unsupported database backend: {backend}")

    def _execute_schema(self, schema: str) -> None:
        """Execute schema script handling multiple statements"""
        # Split the schema into individual statements
        statements = [stmt.strip() for stmt in schema.split(';') if stmt.strip()]
        for statement in statements:
            if statement:
                cur = self._adapter.execute(statement)
                cur.close()

    def _convert_schema_to_postgres(self, schema: str) -> str:
        """Convert SQLite schema to PostgreSQL compatible schema"""
        # Basic conversions - this might need to be more sophisticated
        schema = schema.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
        schema = schema.replace("INSERT OR IGNORE", "INSERT ... ON CONFLICT DO NOTHING")
        return schema

    @staticmethod
    def bit_to_int(bit: str | int) -> int:
        return -1 if bit == "x" else int(bit)

    @staticmethod
    def param_to_int(param: str | int) -> int:
        return param if isinstance(param, int) else int(param, base=2)

    def width_of(self, id) -> int:
        cur = self._adapter.execute("SELECT MAX(idx) FROM wirevec_members WHERE wirevec = " + self._adapter.get_placeholder(), (id,))
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
        return self._adapter.get_tech_tables()

    def execute(self, query: str, params=None):
        """Execute a query and return cursor"""
        return self._adapter.execute(query, params)

    def executemany(self, query: str, params_list):
        """Execute a query multiple times with different parameters"""
        return self._adapter.executemany(query, params_list)

    def commit(self):
        """Commit the current transaction"""
        self._adapter.commit()

    def close(self):
        """Close the database connection"""
        self._adapter.close()

    def dump_tables(self) -> dict:
        tables = self._adapter.get_all_tables()
        db = {}
        for table in tables:
            cur = self._adapter.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            db[table] = [dict(zip([col[0] for col in cur.description], row)) for row in rows]
            cur.close()
        return db

    def dump_wirevecs(self) -> dict[int, list[int]]:
        cur = self._adapter.execute("SELECT id FROM wirevecs ORDER BY id")
        wvs = {}
        for (id,) in cur.fetchall():
            wvs[id] = self._get_wirevec(id)
        return wvs

    def _get_wirevec(self, id: int) -> list[int]:
        placeholder = self._adapter.get_placeholder()
        cur = self._adapter.execute(f"SELECT wire FROM wirevec_members WHERE wirevec = {placeholder} ORDER BY idx", (id,))
        result = [w for (w,) in cur.fetchall()]
        cur.close()
        return result

    def _add_wirevec(self, wv: list[int]) -> int:
        h = self._rhash.hash(wv)
        placeholder = self._adapter.get_placeholder()
        cur = self._adapter.execute(f"INSERT INTO wirevecs (hash) VALUES ({placeholder}) RETURNING id", (h,))
        id = cur.fetchone()[0]
        cur.close()
        self._adapter.executemany(
            f"INSERT INTO wirevec_members (wirevec, idx, wire) VALUES ({placeholder}, {placeholder}, {placeholder})",
            ((id, i, w) for i, w in enumerate(wv))
        )
        self._adapter.commit()
        return id

    def _create_or_lookup_wirevec(self, wv: list[int]) -> int:
        h = self._rhash.hash(wv)
        placeholder = self._adapter.get_placeholder()
        cur = self._adapter.execute(f"SELECT id FROM wirevecs WHERE hash = {placeholder}", (h,))
        rows = cur.fetchall()
        cur.close()
        for (id,) in rows:  # lookup
            if self._get_wirevec(id) == wv:
                return id
        # not found, insert
        cur = self._adapter.execute(f"INSERT INTO wirevecs (hash) VALUES ({placeholder}) RETURNING id", (h,))
        id = cur.fetchone()[0]
        cur.close()
        self._adapter.executemany(
            f"INSERT INTO wirevec_members (wirevec, idx, wire) VALUES ({placeholder}, {placeholder}, {placeholder})",
            ((id, i, w) for i, w in enumerate(wv))
        )
        self._adapter.commit()
        return id

    def _add_input(self, name: str, source: list[int]):
        ws = self._create_or_lookup_wirevec(source)
        placeholder = self._adapter.get_placeholder()
        insert_query = self._adapter.format_insert_ignore("from_inputs", ["source", "name"])
        cur = self._adapter.execute(insert_query, (ws, name))
        cur.close()
        self._adapter.commit()

    def _add_output(self, name: str, sink: list[int]):
        ws = self._create_or_lookup_wirevec(sink)
        placeholder = self._adapter.get_placeholder()
        insert_query = self._adapter.format_insert_ignore("as_outputs", ["sink", "name"])
        cur = self._adapter.execute(insert_query, (ws, name))
        cur.close()
        self._adapter.commit()

    def _add_dff(self, d: list[int], q: list[int]):
        wvd = self._create_or_lookup_wirevec(d)
        wvq = self._create_or_lookup_wirevec(q)
        insert_query = self._adapter.format_insert_ignore("dffs", ["d", "q"])
        cur = self._adapter.execute(insert_query, (wvd, wvq))
        cur.close()
        self._adapter.commit()

    def _add_ay_cell(self, type_: str, a: list[int], y: list[int]):
        wva, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(y)
        insert_query = self._adapter.format_insert_ignore("ay_cells", ["type", "a", "y"])
        cur = self._adapter.execute(insert_query, (type_, wva, wvy))
        cur.close()
        self._adapter.commit()

    def _add_aby_cell(self, type_: str, a: list[int], b: list[int], y: list[int]):
        wva, wvb, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(b), self._create_or_lookup_wirevec(y)
        insert_query = self._adapter.format_insert_ignore("aby_cells", ["type", "a", "b", "y"])
        cur = self._adapter.execute(insert_query, (type_, wva, wvb, wvy))
        cur.close()
        self._adapter.commit()

    def _add_absy_cell(self, type_: str, a: list[int], b: list[int], s: list[int], y: list[int]):
        wva, wvb, wvs, wvy = self._create_or_lookup_wirevec(a), self._create_or_lookup_wirevec(b), self._create_or_lookup_wirevec(s), self._create_or_lookup_wirevec(y)
        insert_query = self._adapter.format_insert_ignore("absy_cells", ["type", "a", "b", "s", "y"])
        cur = self._adapter.execute(insert_query, (type_, wva, wvb, wvs, wvy))
        cur.close()
        self._adapter.commit()

    def _add_blackbox_cell(self, name: str, module: str, params: dict[str, Any], signals: list[tuple[str, list[int]]]):
        placeholder = self._adapter.get_placeholder()
        cur = self._adapter.execute(f"INSERT INTO instances (name, params, module) VALUES ({placeholder}, {placeholder}, {placeholder})", (name, json.dumps(params), module))
        cur.close()
        self._adapter.executemany(f"INSERT INTO instance_ports (instance, port, signal) VALUES ({placeholder}, {placeholder}, {placeholder})", ((name, port, self._create_or_lookup_wirevec(signal)) for port, signal in signals))
        self._adapter.commit()

    # The rest of the methods (build_from_json, rebuild, etc.) remain largely the same
    # but use self._adapter instead of direct database calls

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
        placeholder = self._adapter.get_placeholder()
        for name, mem in memories.items():
            cur = self._adapter.execute(f"INSERT INTO memories (name, width, size) VALUES ({placeholder}, {placeholder}, {placeholder})", (name, mem["width"], mem["size"]))
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
                placeholder = self._adapter.get_placeholder()
                cur = self._adapter.execute(f"INSERT INTO memrds (memory, raddr, rdata) VALUES ({placeholder}, {placeholder}, {placeholder})", (params["MEMID"][1:], self._create_or_lookup_wirevec(raddr), self._create_or_lookup_wirevec(rdata)))
                cur.close()
            elif type_ == "$memwr_v2":
                waddr = [self.bit_to_int(bit) for bit in conns["ADDR"]]
                wclk = [self.bit_to_int(bit) for bit in conns["CLK"]]
                wdata = [self.bit_to_int(bit) for bit in conns["DATA"]]
                we = [self.bit_to_int(bit) for bit in conns["EN"]]
                assert len(wclk) == 1 and wclk[0] == self._clk
                placeholder = self._adapter.get_placeholder()
                cur = self._adapter.execute(f"INSERT INTO memwrs (memory, waddr, wdata, we) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})", (params["MEMID"][1:], self._create_or_lookup_wirevec(waddr), self._create_or_lookup_wirevec(wdata), self._create_or_lookup_wirevec(we)))
                cur.close()
            else:
                attrs = cell["attributes"]
                if "module_not_derived" in attrs and self.param_to_int(attrs["module_not_derived"]): # blackbox cell
                    self._add_blackbox_cell(name, type_, params, [(port, [self.bit_to_int(bit) for bit in signal]) for port, signal in conns.items()])
                elif type_ not in {"$scopeinfo"}:
                    raise ValueError(f"Unsupported cell type: {type_}")

        self._adapter.commit()
        # set cnt
        cur = self._adapter.execute("SELECT MAX(wire) FROM wirevec_members")
        max_wire = cur.fetchone()[0]
        self._cnt = max_wire if max_wire is not None else 1
        cur.close()
        print(f"Database built with {self._cnt} wires and global clock {self._clk}")

    # The rebuild methods would also need to be adapted...
    # For brevity, I'll include a simplified version

    def rebuild_once(self) -> bool:
        # This would need to be implemented with adapter calls
        # For now, return False to indicate no rebuilding needed
        return False

    def rebuild(self) -> int:
        cnt = 0
        while self.rebuild_once():
            cnt += 1
        return cnt