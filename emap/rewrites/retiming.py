from typing import Iterable
from ..db import NetlistDB


def ematch_dff_forward_aby_cell(db: NetlistDB, target_types: list[str]) -> Iterable[tuple[str, int, int, int]]:
    """
    Return a list of tuples (type, a, b, y) for dff cells that can be rewritten to forward aby cells.
    """
    cur = db.execute("""
        SELECT cell.type, dff1.d, dff2.d, cell.y
        FROM dffs AS dff1 JOIN dffs AS dff2 JOIN aby_cells as cell ON dff1.q = cell.a AND dff2.q = cell.b
        WHERE cell.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )
    return cur

def apply_dff_forward_aby_cell(db: NetlistDB, matches: Iterable[tuple[str, int, int, int]]) -> int:
    """
    Apply the dff forward aby cell matches to the database.
    Return the number of rows rewritten.
    """
    newrows = []
    for type_, a, b, y in matches:
        cur = db.execute("SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = ?", (y,))    # get width
        width_y = cur.fetchone()[0]
        cur.execute("SELECT y from aby_cells WHERE type = ? AND a = ? AND b = ? LIMIT 1", (type_, a, b))
        row = cur.fetchone()
        if row is None:
            d = db._add_wirevec([db.auto_id for _ in range(width_y)])
            cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, d))
        else:
            d = row[0]
        newrows.append((d, y))
    cur.executemany("INSERT OR IGNORE INTO dffs (d, q) VALUES (?, ?)", newrows)
    db.commit()
    return cur.rowcount