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
        cur2 = db.execute("SELECT y from aby_cells WHERE type = ? AND a = ? AND b = ? LIMIT 1", (type_, a, b))
        row = cur2.fetchone()
        cur2.close()
        if row is None:
            d = db._add_wirevec([db.auto_id for _ in range(width_y)])
            cur2 = db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, d))
            cur2.close()
        else:
            d = row[0]
        newrows.append((d, y))
    cur = db.executemany("INSERT OR IGNORE INTO dffs (d, q) VALUES (?, ?)", newrows)
    db.commit()
    return cur.rowcount


def ematch_dff_backward_aby_cell(db: NetlistDB, target_types: list[str]) -> Iterable[tuple[str, int, int, int]]:
    """
    Return a list of tuples (type, a, b, y) for dff cells that can be rewritten to backward aby cells.
    """
    cur = db.execute("""
        SELECT cell.type, cell.a, cell.b, dff.q
        FROM dffs AS dff JOIN aby_cells as cell ON dff.d = cell.y
        WHERE cell.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )
    return cur

def apply_dff_backward_aby_cell(db: NetlistDB, matches: Iterable[tuple[str, int, int, int]]) -> int:
    """
    Apply the dff backward aby cell matches to the database.
    Return the number of rows rewritten.
    """
    newrows = []
    for type_, a, b, q in matches:
        cur = db.execute("SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = ?", (a,))    # get width
        width_a = cur.fetchone()[0]
        cur2 = db.execute("SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = ?", (b,))
        width_b = cur2.fetchone()[0]
        cur2.close()
        # insert new dffs if not exist
        cur2 = db.execute("SELECT q FROM dffs WHERE d = ? LIMIT 1", (a,))
        row = cur2.fetchone()
        cur2.close()
        if row is None:
            a_q = db._add_wirevec([db.auto_id for _ in range(width_a)])
            cur2 = db.execute("INSERT INTO dffs (d, q) VALUES (?, ?)", (a, a_q))
            cur2.close()
        else:
            a_q = row[0]
        cur2 = db.execute("SELECT q FROM dffs WHERE d = ? LIMIT 1", (b,))
        row = cur2.fetchone()
        cur2.close()
        if row is None:
            b_q = db._add_wirevec([db.auto_id for _ in range(width_b)])
            cur2 = db.execute("INSERT INTO dffs (d, q) VALUES (?, ?)", (b, b_q))
            cur2.close()
        else:
            b_q = row[0]
        newrows.append((type_, a_q, b_q, q))
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()
    return cur.rowcount


def rewrite_sdff(db: NetlistDB) -> int:
    """
    This is a final pass before techmapping to rewrite a $dff and a $mux to a $sdff.
    Return the number of rows rewritten.
    """
    # dynamically create the table for $sdff
    db.execute("""
        CREATE TABLE IF NOT EXISTS sdffs (
            d INTEGER,
            q INTEGER,
            rst INTEGER,
            rst_val INTEGER,    -- this is the actual constant value, not wirevec id
            PRIMARY KEY(d, rst, rst_val),
            FOREIGN KEY (d) REFERENCES wirevecs(id),
            FOREIGN KEY (q) REFERENCES wirevecs(id),
            FOREIGN KEY (rst) REFERENCES wirevecs(id)
        );
    """)

    cur = db.execute("""
        SELECT mux.a, dff.q, mux.s, mux.b
        FROM absy_cells AS mux JOIN dffs AS dff ON mux.y = dff.d
        WHERE mux.type = '$mux'
    """)
    newrows = []
    for d, q, rst, rst_wvid in cur:
        rst_wv = db._get_wirevec(rst_wvid)
        rst_val = db.vec_to_const(rst_wv)
        if rst_val is not None:
            newrows.append((d, q, rst, rst_val))
    cur = db.executemany("INSERT OR IGNORE INTO sdffs (d, q, rst, rst_val) VALUES (?, ?, ?, ?)", newrows)
    db.commit()
    return cur.rowcount