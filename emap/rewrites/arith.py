from typing import Iterable
from ..db import NetlistDB


def ematch_unsigned_add_to_signed(db: NetlistDB) -> Iterable[tuple[int, int, int]]:
    """
    Return a list of tuples (a, b, y).
    NOTE: this only matches when width(a) <= width(y) and width(b) <= width(y).
    The sufficient condition for $unsigned(a) + $unsigned(b) == $signed(a) + $signed(b) is that if truncating $unsigned(a) and $signed(a) to width(y) gives the same result, and similarly for b.
    """
    cur = db.execute("""
        SELECT a, b, y
        FROM aby_cells
        WHERE aby_cells.type = '$addu'
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.a) <= (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.y)
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.b) <= (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.y)
    """)
    return cur

def apply_unsigned_add_to_signed(db: NetlistDB, matches: Iterable[tuple[int, int, int]]) -> int:
    """
    Return the number of rows rewritten.
    """
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES ('$adds', ?, ?, ?)", matches)
    db.commit()
    return cur.rowcount


def apply_signed_arith_input_trunc(db: NetlistDB, matches: Iterable[tuple[str, int, int, int]]) -> int:
    """
    Return the number of rows rewritten.
    NOTE: the matches should be signed arithmetic cells, e.g. $adds, $muls.
    """
    newrows = []
    for type, a, b, y in matches:
        awv, bwv = db._get_wirevec(a), db._get_wirevec(b)
        while len(awv) > 1 and awv[-1] == awv[-2]:
            awv.pop()
        while len(bwv) > 1 and bwv[-1] == bwv[-2]:
            bwv.pop()
        newrows.append((type, db._create_or_lookup_wirevec(awv), db._create_or_lookup_wirevec(bwv), y))
    cur = db.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    db.commit()
    return cur.rowcount


def _construct_unsigned_adder(db: NetlistDB, a: list[int], b: list[int], y: list[int], cin: int, index: int = 0) -> bool:
    """
    Construct an unsigned adder for a + b = y with carry-in cin.
    Return True if successful, False otherwise.
    """
    if index >= len(y):
        return False
    awv = db._create_or_lookup_wirevec([a[index]])
    bwv = db._create_or_lookup_wirevec([b[index]])
    ywv = db._create_or_lookup_wirevec([y[index]])

    modified = False

    # build y[index] = a[index] ^ b[index] ^ cin
    cur = db.execute("SELECT y FROM aby_cells WHERE type = '$xor' AND a = ? AND b = ?", (awv, bwv))
    row = cur.fetchone()
    if row is None:
        modified = True
        a_xor_b = db._create_or_lookup_wirevec([db.auto_id])
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$xor', ?, ?, ?)", (awv, bwv, a_xor_b))
    else:
        a_xor_b = row[0]
    cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES ('$xor', ?, ?, ?)", (a_xor_b, db._create_or_lookup_wirevec([cin]), ywv))
    modified |= cur.rowcount > 0

    # build cout = (a[index] & b[index]) | (cin & (a[index] ^ b[index]))
    cur = db.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = ? AND b = ?", (awv, bwv))
    row = cur.fetchone()
    if row is None:
        modified = True
        a_and_b = db._create_or_lookup_wirevec([db.auto_id])
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", (awv, bwv, a_and_b))
    else:
        a_and_b = row[0]
    cur = db.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = ? AND b = ?", (db._create_or_lookup_wirevec([cin]), a_xor_b))
    row = cur.fetchone()
    if row is None:
        modified = True
        cin_and_a_xor_b = db._create_or_lookup_wirevec([db.auto_id])
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", (db._create_or_lookup_wirevec([cin]), a_xor_b, cin_and_a_xor_b))
    else:
        cin_and_a_xor_b = row[0]
    cur.execute("SELECT y FROM aby_cells WHERE type = '$or' AND a = ? AND b = ?", (a_and_b, cin_and_a_xor_b))
    row = cur.fetchone()
    if row is None:
        modified = True
        cout = db.auto_id
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$or', ?, ?, ?)", (a_and_b, cin_and_a_xor_b, db._create_or_lookup_wirevec([cout])))
    else:
        coutwv = row[0]
        cout = db._get_wirevec(coutwv)[0]

    db.commit()
    modified |= _construct_unsigned_adder(db, a, b, y, cout, index + 1)
    return modified

def apply_unsigned_add_bitblast(db: NetlistDB, matches: Iterable[tuple[int, int, int]]) -> int:
    """
    Return the number of rows rewritten.
    """
    cnt = 0
    for a, b, y in matches:
        awv, bwv, ywv = db._get_wirevec(a), db._get_wirevec(b), db._get_wirevec(y)
        # zero-extend or truncate a and b to the width of y
        awv = awv + [0] * (len(ywv) - len(awv)) if len(awv) < len(ywv) else awv[:len(ywv)]
        bwv = bwv + [0] * (len(ywv) - len(bwv)) if len(bwv) < len(ywv) else bwv[:len(ywv)]
        cnt += _construct_unsigned_adder(db, awv, bwv, ywv, 0)
    return cnt