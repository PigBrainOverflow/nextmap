import sqlite3


class NetlistDB(sqlite3.Connection):
    ABY_CELL_TYPES = {
        "$add", "$sub", "$mul",
        "$and", "$or"
    }

    cnt: int

    # auxiliary functions
    @staticmethod
    def bitvec_to_int(bv: list[int]) -> int:
        return sum((1 << i) * b for i, b in enumerate(bv))

    @staticmethod
    def bitvec_to_bool(bv: list[int]) -> bool:
        return sum(bv) > 0

    def next_id(self) -> int:
        self.cnt += 1
        return self.cnt

    # database raw operations
    def _width_of(self, id: str) -> int | None:
        cursor = self.execute("SELECT width FROM wires WHERE id = ?", (id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def _insert_wire(self, id: str, width: int = -1):
        self.execute("INSERT INTO wires (id, width) VALUES (?, ?)", (id, width))

    def _insert_external_port(self, wire: str, direction: str | None = None):
        self.execute("INSERT INTO external_ports (wire, direction) VALUES (?, ?)", (wire, direction))

    def _insert_ay_cell(self, type_: str, a: str, y: str):
        self.execute("INSERT INTO ay_cells (type, a, y) VALUES (?, ?, ?)", (type_, a, y))

    # insert when not exists
    def get_slice(self, source: str, low: int, high: int) -> str:
        # return wire id
        # check if slice already exists
        cursor = self.execute("SELECT id FROM slices WHERE source = ? AND low = ? AND high = ?", (source, low, high))
        row = cursor.fetchone()
        if row:
            return row[0]
        # create new slice
        id = self.next_id()
        self.execute("INSERT INTO wires (id, width) VALUES (?, ?)", (id, high - low + 1))
        self.execute("INSERT INTO slices (source, low, high, sink) VALUES (?, ?, ?, ?)", (source, low, high, id))
        return id

    # insert when not exists
    def get_chunk(self, chunk: dict) -> str:
        # return wire or const id
        type_ = chunk["type"]
        if type_ == "wire":
            id, offset, width = chunk["id"], chunk["offset"], chunk["width"]
            if offset == 0 and self._width_of(id) == width: # no offset and width matches
                return id
            # need slice (extract)
            return self.get_slice(id, offset, offset + width - 1)
        elif type_ == "const":
            value, width = chunk["value"], chunk["width"]
            id = f"const_{value}_{width}"
            self.execute("INSERT OR IGNORE INTO consts (id, value, width) VALUES (?, ?, ?)", (id, value, width))
            return id
        else:
            raise ValueError(f"Unsupported chunk type: {type_}")

    def create_sig(self, chunks: list) -> str:
        # return the new wire or const id
        if len(chunks) == 1:    # single wire
            return self.get_chunk(chunks[0])
        # need slice (concatenate)
        source, cur_offset = self.next_id(), 0
        for chunk in chunks:
            id = self.get_chunk(chunk)
            width = self._width_of(id)
            assert width is not None
            self.execute("INSERT INTO connects (source, low, high, sink) VALUES (?, ?, ?, ?)", (source, cur_offset, cur_offset + width - 1, id))
            cur_offset += width
        self._insert_wire(source, cur_offset)
        return source

    def __init__(self, schema_file: str = "schema.sql", db_file: str = ":memory:"):
        super().__init__(db_file)
        with open(schema_file, "r") as f:
            self.executescript(f.read())
        self.cnt = 0

    def build_from_rtlil(self, rtlil_mod: dict):
        wires, cells, conns = rtlil_mod["wires"], rtlil_mod["cells"], rtlil_mod["connects"]

        # build wires
        for wire in wires:
            id, width = wire["name"], wire["width"]
            self._insert_wire(id, width)
            if wire["port_input"]:
                self._insert_external_port(id, "input")
            if wire["port_output"]:
                self._insert_external_port(id, "output")
        self.commit()

        # build cells
        for cell in cells:
            type_, params, connects = cell["type"], cell["parameters"], cell["connects"]
            if type_ in {"$add", "$sub", "$mul"}:
                extended_a, extended_b = self.next_id(), self.next_id()
                self._insert_wire(extended_a)
                self._insert_wire(extended_b)
                if NetlistDB.bitvec_to_bool(params["\\A_SIGNED"]) and NetlistDB.bitvec_to_bool(params["\\B_SIGNED"]): # signed
                    self._insert_ay_cell("sign_extend", )
            elif type_ in NetlistDB.ABY_CELL_TYPES:
                pass
            else:
                raise ValueError(f"Unsupported cell type: {type_}")