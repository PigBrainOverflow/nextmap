from typing import Iterable
from ..db import NetlistDB


def ematch_comm(db: NetlistDB, target_types: list[str]) -> Iterable[tuple[str, int, int, int]]:
    """
    Return a list of tuples (type, a, b, y) for commutative cells.
    """
    cur = db.execute(
        "SELECT type, a, b, y FROM aby_cells WHERE type IN ({})".format(",".join("?" * len(target_types))),
        target_types
    )
    return cur

def apply_comm(db: NetlistDB, matches: Iterable[tuple[str, int, int, int]]) -> int:
    """
    Return the number of rows rewritten by applying commutative matches.
    """
    matches = list(matches) # for debug
    cur = db.executemany(
        "INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)",
        ((type_, b, a, y) for type_, a, b, y in matches)
    )
    db.commit()
    return cur.rowcount


def ematch_assoc_to_right(db: NetlistDB, target_types: list[str]) -> Iterable[tuple[str, int, int, int, int]]:
    """
    Return a list of tuples (type, a, b, y) for associative cells that can be rewritten to right associative form.
    E.g. (a + b) + c => a + (b + c)
    NOTE: The width of b + c should be the same as (a + b) + c to preserve the semantics.
    """
    cur = db.execute("""
        SELECT cell1.type, cell1.a, cell1.b, cell2.b, cell2.y
        FROM aby_cells AS cell1 JOIN aby_cells AS cell2 ON cell1.y = cell2.a
        WHERE cell1.type = cell2.type AND cell1.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )
    return cur

def apply_assoc_to_right(db: NetlistDB, matches: Iterable[tuple[str, int, int, int, int]]) -> int:
    """
    Apply the associative matches to the database.
    Return the number of rows rewritten.
    """
    newrows = []
    for type_, a, b, c, y in matches:
        cur = db.execute("SELECT MAX(idx) FROM wirevec_members WHERE wirevec = ?", (y,))
        width_b_add_c = cur.fetchone()[0] + 1
        cur.execute(
            "SELECT y FROM aby_cells WHERE type = ? AND a = ? AND b = ? AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = y) = ? LIMIT 1",
            (type_, b, c, width_b_add_c)
        )
        row = cur.fetchone()
        if row is None:
            b_add_c = db._add_wirevec([db.auto_id for _ in range(width_b_add_c)])
            cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, b, c, b_add_c))
        else:
            b_add_c = row[0]
        newrows.append((type_, a, b_add_c, y))
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()
    return cur.rowcount


def ematch_assoc_to_left(db: NetlistDB, target_types: list[str]) -> Iterable[tuple[str, int, int, int, int]]:
    """
    Return a list of tuples (type, a, b, y) for associative cells that can be rewritten to left associative form.
    E.g. a + (b + c) => (a + b) + c
    NOTE: The width of a + b should be the same as a + (b + c) to preserve the semantics.
    """
    cur = db.execute("""
        SELECT cell1.type, cell1.a, cell1.b, cell2.b, cell2.y
        FROM aby_cells AS cell1 JOIN aby_cells AS cell2 ON cell1.y = cell2.a
        WHERE cell1.type = cell2.type AND cell1.type IN ({})
        """.format(",".join("?" * len(target_types))),
        target_types
    )
    return cur

def apply_assoc_to_left(db: NetlistDB, matches: Iterable[tuple[str, int, int, int, int]]) -> int:
    """
    Apply the associative matches to the database.
    Return the number of rows rewritten.
    """
    newrows = []
    for type_, a, b, c, y in matches:
        cur = db.execute("SELECT MAX(idx) FROM wirevec_members WHERE wirevec = ?", (y,))
        width_a_add_b = cur.fetchone()[0] + 1
        cur.execute(
            "SELECT y FROM aby_cells WHERE type = ? AND a = ? AND b = ? AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = y) = ? LIMIT 1",
            (type_, a, b, width_a_add_b)
        )
        row = cur.fetchone()
        if row is None:
            a_add_b = db._add_wirevec([db.auto_id for _ in range(width_a_add_b)])
            cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, a, b, a_add_b))
        else:
            a_add_b = row[0]
        newrows.append((type_, a_add_b, c, y))
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()
    return cur.rowcount


def ematch_distr_fold(db: NetlistDB) -> Iterable[tuple[int, int, int, int]]:
    """
    Return a list of tuples (a, b, c, y) for distributive cells that can be rewritten to folded form.
    E.g. a * b + a * c => a * (b + c)
    """
    cur = db.execute("""
        SELECT mul1.a, mul1.b, mul2.b, add1.y
        FROM aby_cells AS mul1 JOIN aby_cells AS mul2 JOIN aby_cells AS add1
        ON mul1.a = mul2.a AND mul1.y = add1.a AND mul2.y = add1.b
        WHERE mul1.type = '$muls' AND mul2.type = '$muls' AND add1.type = '$adds'
    """)
    return cur

def apply_distr_fold(db: NetlistDB, matches: Iterable[tuple[int, int, int, int]]) -> int:
    newrows = []
    for a, b, c, y in matches:
        cur = db.execute("SELECT MAX(idx) FROM wirevec_members WHERE wirevec = ?", (a,))
        width_a = cur.fetchone()[0] + 1
        cur.execute(
            "SELECT y FROM aby_cells WHERE type = '$adds' AND a = ? AND b = ? AND width_of(a) = ? AND width_of(b) = ? AND width_of(y) = ? LIMIT 1",
            (b, c, width_a, width_a, width_a + 1)
        )
        row = cur.fetchone()
        if row is None:
            b_add_c = db._add_wirevec([db.auto_id for _ in range(width_a + 1)])
            cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', ?, ?, ?)", (b, c, b_add_c))
        else:
            b_add_c = row[0]
        newrows.append(("$muls", a, b_add_c, y))
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()
    return cur.rowcount