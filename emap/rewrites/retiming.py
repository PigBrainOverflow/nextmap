from ..db import NetlistDB


"""
retiming rewrites for dff cells
"""

def rewrite_dff_forward_aby_cell(db: NetlistDB, target_types: list[str], subsume: bool = False) -> int:
    """
    FROM
    -> dff -> aby_cell ->
    -> dff ->
    TO
    -> aby_cell -> dff ->
    ->
    """
    assert not subsume, "Subsumption is not supported for retiming rewrites"

    cur = db.execute("""
        SELECT cell.type, dff1.clk, dff1.d, dff2.d, cell.y
        FROM dffs AS dff1 JOIN dffs AS dff2 JOIN aby_cells as cell ON dff1.q = cell.a AND dff2.q = cell.b AND dff1.clk = dff2.clk
        WHERE cell.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )

    # first, build aby_cell if not exists
    rows = cur.fetchall()
    newrows = []
    for type_, clk, a, b, y in rows:
        cur.execute("SELECT y from aby_cells WHERE type = ? AND a = ? AND b = ?", (type_, a, b))
        res = cur.fetchone()
        if res is None:
            aby_cell_y = db.next_wires(NetlistDB.width_of(y))
            cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, aby_cell_y))
        else:
            aby_cell_y = res[0]
        newrows.append((aby_cell_y, clk, y))
    cur.executemany("INSERT OR IGNORE INTO dffs (d, clk, q) VALUES (?, ?, ?)", newrows)
    db.commit()

    return cur.rowcount

def rewrite_dff_backward_aby_cell(db: NetlistDB, target_types: list[str], subsume: bool = False) -> int:
    """
    FROM
    -> aby_cell -> dff ->
    ->
    TO
    -> dff -> aby_cell ->
    -> dff ->
    """
    assert not subsume, "Subsumption is not supported for retiming rewrites"

    cur = db.execute("""
        SELECT cell.type, dff.clk, cell.a, cell.b, dff.q
        FROM dffs AS dff JOIN aby_cells as cell ON dff.d = cell.y
        WHERE cell.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )
    newrows = []
    for type_, clk, a, b, y in cur.fetchall():
        dffa = db.find_or_create_dff(NetlistDB.width_of(a), a, clk)
        dffb = db.find_or_create_dff(NetlistDB.width_of(b), b, clk)
        newrows.append((type_, dffa, dffb, y))
    cur.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()

    return cur.rowcount

def rewrite_split_wide_dff(db: NetlistDB, width: int, subsume: bool = False) -> int:
    """
    Split dff into two dffs if the width is larger than `width`
    """
    assert not subsume, "Subsumption is not supported for split dff rewrites"

    cur = db.execute("SELECT d, clk, q FROM dffs WHERE width_of(d) > ?", (width,))

    cnt = 0
    for d, clk, q in cur.fetchall():
        d1, d2 = d.split(",")[:width], d.split(",")[width:]
        q1, q2 = q.split(",")[:width], q.split(",")[width:]
        cur.execute("INSERT OR IGNORE INTO dffs (d, clk, q) VALUES (?, ?, ?)", (",".join(d1), clk, ",".join(q1)))
        cur.execute("INSERT OR IGNORE INTO dffs (d, clk, q) VALUES (?, ?, ?)", (",".join(d2), clk, ",".join(q2)))
        cnt += cur.rowcount > 0

    db.commit()
    return cnt