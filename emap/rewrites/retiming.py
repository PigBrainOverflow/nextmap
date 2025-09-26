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
        """.format(",".join("%s" * len(target_types))),
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
        cur = db.execute("SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = %s", (y,))    # get width
        width_y = cur.fetchone()[0]
        cur.execute("SELECT y from aby_cells WHERE type = %s AND a = %s AND b = %s LIMIT 1", (type_, a, b))
        row = cur.fetchone()
        if row is None:
            d = db._add_wirevec([db.auto_id for _ in range(width_y)])
            cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s)", (type_, a, b, d))
        else:
            d = row[0]
        newrows.append((d, y))
    cur = db.executemany("INSERT OR IGNORE INTO dffs (d, q) VALUES (%s, %s)", newrows)
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
        """.format(",".join("%s" * len(target_types))),
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
        cur = db.execute("SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = %s", (a,))    # get width
        width_a = cur.fetchone()[0]
        cur.execute("SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = %s", (b,))    # get width
        width_b = cur.fetchone()[0]
        # insert new dffs if not exist
        cur.execute("SELECT q FROM dffs WHERE d = %s LIMIT 1", (a,))
        row = cur.fetchone()
        if row is None:
            a_q = db._add_wirevec([db.auto_id for _ in range(width_a)])
            cur.execute("INSERT INTO dffs (d, q) VALUES (%s, %s)", (a, a_q))
        else:
            a_q = row[0]
        cur.execute("SELECT q FROM dffs WHERE d = %s LIMIT 1", (b,))
        row = cur.fetchone()
        if row is None:
            b_q = db._add_wirevec([db.auto_id for _ in range(width_b)])
            cur.execute("INSERT INTO dffs (d, q) VALUES (%s, %s)", (b, b_q))
        else:
            b_q = row[0]
        newrows.append((type_, a_q, b_q, q))
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s)", newrows)
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
    cur = db.executemany("INSERT OR IGNORE INTO sdffs (d, q, rst, rst_val) VALUES (%s, %s, %s, %s)", newrows)
    db.commit()
    return cur.rowcount