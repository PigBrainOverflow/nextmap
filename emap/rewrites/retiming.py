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