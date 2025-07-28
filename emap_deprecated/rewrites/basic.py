from ..db import NetlistDB


"""
basic rewrites for logic and arithmetic cells
"""

def rewrite_comm(db: NetlistDB, target_types: list[str], subsume: bool = False) -> int:
    # return the number of rows rewritten
    assert not subsume, "Subsumption is not supported for commutative arithmetic cells"

    cur = db.execute("SELECT type, a, b, y FROM aby_cells WHERE type IN ({})".format(",".join("?" * len(target_types))), target_types)
    newrows = [(type_, b, a, y) for type_, a, b, y in cur]
    cur.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()

    return cur.rowcount

def rewrite_assoc_to_right(db: NetlistDB, target_types: list[str], subsume: bool = False) -> int:
    # return the number of rows rewritten
    # e.g. (a + b) + c => a + (b + c)
    # NOTE: the width of b + c would be the same as (a + b) + c to preserve the semantics
    assert not subsume, "Subsumption is not supported for associative arithmetic cells"

    cur = db.execute("""
        SELECT cell1.type, cell1.a, cell1.b, cell2.b, cell2.y
        FROM aby_cells AS cell1 JOIN aby_cells AS cell2 ON cell1.y = cell2.a
        WHERE cell1.type = cell2.type AND cell1.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )

    # first, build b + c if not exists
    rows = cur.fetchall()
    newrows = []
    for type_, a, b, c, y in rows:
        cur.execute("SELECT y from aby_cells WHERE type = ? AND a = ? AND b = ?", (type_, b, c))
        res = cur.fetchone()
        if res is None:   # not exists
            b_add_c = db.next_wires(NetlistDB.width_of(y))
            cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, b, c, b_add_c))
        else:
            b_add_c = res[0]
        newrows.append((type_, a, b_add_c, y))
    cur.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()

    return cur.rowcount