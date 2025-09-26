from typing import Iterable
from ..db import NetlistDB


def ematch_word_dff(db: NetlistDB) -> Iterable[tuple[int, int]]:
    """
    Return a list of tuples (d, q).
    """
    cur = db.execute("""
        SELECT dff.d, dff.q
        FROM dffs AS dff
        WHERE (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = dff.d) > 1
    """)
    return cur

def apply_word_dff_split(db: NetlistDB, matches: Iterable[tuple[int, int]]) -> int:
    """
    Apply the word dff split matches to the database.
    Return the number of rows rewritten.
    NOTE: this will not delete the original word dff rows.
    """
    cnt = 0
    for d, q in matches:
        dwv, qwv = db._get_wirevec(d), db._get_wirevec(q)
        assert len(dwv) == len(qwv)
        modified = False
        for dw, qw in zip(dwv, qwv):
            cur = db.execute("INSERT OR IGNORE INTO dffs (d, q) VALUES (%s, %s)", (db._create_or_lookup_wirevec([dw]), db._create_or_lookup_wirevec([qw])))
            modified |= cur.rowcount > 0
        cnt += modified

    db.commit()
    return cnt


def ematch_wide_dff(db: NetlistDB, width_threshold: int = 16) -> Iterable[tuple[int, int]]:
    """
    Return a list of tuples (d, q).
    """
    cur = db.execute("""
        SELECT dff.d, dff.q
        FROM dffs AS dff
        WHERE (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = dff.d) > %s
    """, (width_threshold,))
    return cur

def apply_wide_dff_split(db: NetlistDB, matches: Iterable[tuple[int, int]], width_threshold: int = 16) -> int:
    """
    Apply the wide dff split matches to the database.
    Return the number of rows rewritten.
    NOTE: this will not delete the original wide dff rows.
    """
    cnt = 0
    for d, q in matches:
        dwv, qwv = db._get_wirevec(d), db._get_wirevec(q)
        assert len(dwv) == len(qwv)
        assert len(dwv) > width_threshold
        modified = False
        dwv_lo, dwv_hi = dwv[:width_threshold], dwv[width_threshold:]
        qwv_lo, qwv_hi = qwv[:width_threshold], qwv[width_threshold:]
        cur = db.execute("INSERT OR IGNORE INTO dffs (d, q) VALUES (%s, %s)", (db._create_or_lookup_wirevec(dwv_lo), db._create_or_lookup_wirevec(qwv_lo)))
        modified |= cur.rowcount > 0
        cur = db.execute("INSERT OR IGNORE INTO dffs (d, q) VALUES (%s, %s)", (db._create_or_lookup_wirevec(dwv_hi), db._create_or_lookup_wirevec(qwv_hi)))
        modified |= cur.rowcount > 0
        cnt += modified

    db.commit()
    return cnt