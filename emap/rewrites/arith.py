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


def select_aby_cell_by_type(db: NetlistDB, targets: list[str]) -> Iterable[tuple[str, int, int, int]]:
    """
    Return a list of tuples (type, a, b, y).
    """
    cur = db.execute(f"""
        SELECT type, a, b, y
        FROM aby_cells
        WHERE aby_cells.type IN ({','.join(['?'] * len(targets))})
    """, targets)
    return cur

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