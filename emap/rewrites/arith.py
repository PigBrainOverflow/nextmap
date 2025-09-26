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
    cur = db.executemany("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s) ON CONFLICT DO NOTHING", matches)
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
    cur = db.executemany("INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", newrows)
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
    cur = db.execute("SELECT y FROM aby_cells WHERE type = '$xor' AND a = %s AND b = %s", (awv, bwv))
    row = cur.fetchone()
    if row is None:
        modified = True
        a_xor_b = db._create_or_lookup_wirevec([db.auto_id])
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$xor', %s, %s, %s)", (awv, bwv, a_xor_b))
    else:
        a_xor_b = row[0]
    cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$xor', %s, %s, %s) ON CONFLICT DO NOTHING", (a_xor_b, db._create_or_lookup_wirevec([cin]), ywv))
    modified |= cur.rowcount > 0

    # build cout = (a[index] & b[index]) | (cin & (a[index] ^ b[index]))
    cur = db.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = %s AND b = %s", (awv, bwv))
    row = cur.fetchone()
    if row is None:
        modified = True
        a_and_b = db._create_or_lookup_wirevec([db.auto_id])
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', %s, %s, %s)", (awv, bwv, a_and_b))
    else:
        a_and_b = row[0]
    cur = db.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = %s AND b = %s", (db._create_or_lookup_wirevec([cin]), a_xor_b))
    row = cur.fetchone()
    if row is None:
        modified = True
        cin_and_a_xor_b = db._create_or_lookup_wirevec([db.auto_id])
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', %s, %s, %s)", (db._create_or_lookup_wirevec([cin]), a_xor_b, cin_and_a_xor_b))
    else:
        cin_and_a_xor_b = row[0]
    cur.execute("SELECT y FROM aby_cells WHERE type = '$or' AND a = %s AND b = %s", (a_and_b, cin_and_a_xor_b))
    row = cur.fetchone()
    if row is None:
        modified = True
        cout = db.auto_id
        db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$or', %s, %s, %s)", (a_and_b, cin_and_a_xor_b, db._create_or_lookup_wirevec([cout])))
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


def ematch_wide_mulu(db: NetlistDB, a_width: int, b_width: int) -> Iterable[tuple[int, int, int]]:
    """
    Return a list of tuples (a, b, y).
    width(b) > b_width and width(a) <= a_width.
    """
    cur = db.execute("""
        SELECT a, b, y
        FROM aby_cells
        WHERE type = '$mulu'
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.a) <= %s
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.b) > %s
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.y) > %s
    """, (a_width, b_width, b_width))
    return cur

def apply_wide_mulu_split(db: NetlistDB, matches: Iterable[tuple[int, int, int]], a_width: int, b_width: int) -> int:
    """
    Return the number of rows rewritten.
    """
    cnt = 0
    for a, b, y in matches:
        bwv, ywv = db._get_wirevec(b), db._get_wirevec(y)
        blo, bhi = bwv[:a_width], bwv[a_width:]
        ylo, yhi = ywv[:a_width], ywv[a_width:]
        ablo = [db.auto_id for _ in range(len(ywv) - a_width)] + ylo
        ablo = db._create_or_lookup_wirevec(ablo)
        cur = db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$mulu', %s, %s, %s)", (a, db._create_or_lookup_wirevec(blo), ablo))
        cur.execute("SELECT y FROM aby_cells WHERE type = '$mulu' AND a = %s AND b = %s", (a, db._create_or_lookup_wirevec(bhi)))
        row = cur.fetchone()
        if row is None:
            abhi = db._create_or_lookup_wirevec([db.auto_id for _ in range(len(ywv) - a_width)])
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$mulu', %s, %s, %s)", (a, db._create_or_lookup_wirevec(bhi), abhi))
        else:
            abhi = row[0]
        cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$addu', %s, %s, %s)", (abhi, ablo, db._create_or_lookup_wirevec(yhi)))
        cnt += cur.rowcount > 0
    db.commit()
    return cnt


def ematch_complex_mul(db: NetlistDB) -> Iterable[tuple[int, int, int, int, int, int]]:
    """
    Return a list of tuples (a, b, c, d, y1, y2) that matches the pattern:
        y1 = a*c - b*d
        y2 = a*d + b*c
    """
    cur = db.execute("""
        SELECT mul1.a, mul2.a, mul2.b, mul1.b, add1.y, sub1.y
        FROM aby_cells AS add1 JOIN aby_cells AS mul1 JOIN aby_cells AS mul2
            JOIN aby_cells AS sub1 JOIN aby_cells AS mul3 JOIN aby_cells AS mul4
        ON add1.a = mul1.y AND add1.b = mul2.y AND sub1.a = mul3.y AND sub1.b = mul4.y
            AND mul1.a = mul3.a AND mul1.b = mul4.b AND mul2.a = mul4.a AND mul2.b = mul3.b
        WHERE add1.type = '$adds' AND mul1.type = '$muls' AND mul2.type = '$muls'
            AND sub1.type = '$subs' AND mul3.type = '$muls' AND mul4.type = '$muls'
            AND width_of(mul1.a) = width_of(mul2.a) AND width_of(mul1.b) = width_of(mul2.b)
            AND width_of(mul1.y) = width_of(mul2.y)
    """)
    return cur

def apply_complex_mul(db: NetlistDB, matches: Iterable[tuple[int, int, int, int, int, int]]) -> int:
    """
    Return the number of rows rewritten.
    """
    cnt = 0
    for a, b, c, d, y1, y2 in matches:
        a_width, y1_width, c_width, y2_width = NetlistDB.width_of(db, a), NetlistDB.width_of(db, y1), NetlistDB.width_of(db, c), NetlistDB.width_of(db, y2)
        cur = db.execute("SELECT y FROM aby_cells WHERE type = '$subs' AND a = %s AND b = %s", (a, b))
        row = cur.fetchone()
        if row is None:
            a_sub_b = [db.auto_id for _ in range(a_width)]
            a_sub_b = db._create_or_lookup_wirevec(a_sub_b)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$subs', %s, %s, %s)", (a, b, a_sub_b))
        else:
            a_sub_b = row[0]

        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (a_sub_b, d))
        row = cur.fetchone()
        if row is None:
            factor = [db.auto_id for _ in range(y1_width)]
            factor = db._create_or_lookup_wirevec(factor)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (a_sub_b, d, factor))
        else:
            factor = row[0]

        cur.execute("SELECT y FROM aby_cells WHERE type = '$subs' AND a = %s AND b = %s", (c, d))
        row = cur.fetchone()
        if row is None:
            c_sub_d = [db.auto_id for _ in range(c_width)]
            c_sub_d = db._create_or_lookup_wirevec(c_sub_d)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$subs', %s, %s, %s)", (c, d, c_sub_d))
        else:
            c_sub_d = row[0]

        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (c_sub_d, a))
        row = cur.fetchone()
        if row is None:
            factor1 = [db.auto_id for _ in range(y1_width)]
            factor1 = db._create_or_lookup_wirevec(factor1)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (c_sub_d, a, factor1))
        else:
            factor1 = row[0]

        cur.execute("SELECT y FROM aby_cells WHERE type = '$adds' AND a = %s AND b = %s", (c, d))
        row = cur.fetchone()
        if row is None:
            c_add_d = [db.auto_id for _ in range(c_width)]
            c_add_d = db._create_or_lookup_wirevec(c_add_d)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (c, d, c_add_d))
        else:
            c_add_d = row[0]

        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (c_add_d, b))
        row = cur.fetchone()
        if row is None:
            factor2 = [db.auto_id for _ in range(y2_width)]
            factor2 = db._create_or_lookup_wirevec(factor2)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (c_add_d, b, factor2))
        else:
            factor2 = row[0]

        cur = db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s)", ("$adds", factor, factor1, y1))
        cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (%s, %s, %s, %s)", ("$adds", factor, factor2, y2))
        cnt += cur.rowcount > 0

    db.commit()
    return cnt


def ematch_wide_muls(db: NetlistDB, a_width: int = 32, b_width: int = 32, y_width: int = 64) -> Iterable[tuple[int, int, int]]:
    assert a_width == 32 and b_width == 32 and y_width == 64, "Currently only support 32-bit wide muls"
    cur = db.execute("""
        SELECT a, b, y
        FROM aby_cells
        WHERE type = '$muls'
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.a) = %s
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.b) = %s
            AND (SELECT COUNT(*) FROM wirevec_members WHERE wirevec = aby_cells.y) = %s
    """, (a_width, b_width, y_width))
    return cur

def apply_wide_muls_split(db: NetlistDB, matches: Iterable[tuple[int, int, int]], a_width: int = 32, b_width: int = 32, y_width: int = 64) -> int:
    """
    p0 = a_lo * b_lo
    p1 = (a_lo + a_hi) * (b_lo + b_hi)
    p2 = a_hi * b_hi
    y = p0 + ((p1 - p0 - p2) << 16) + (p2 << 32)
    """
    assert a_width == 32 and b_width == 32 and y_width == 64, "Currently only support 32-bit wide muls"
    cnt = 0
    for a, b, y in matches:
        awv, bwv, ywv = db._get_wirevec(a), db._get_wirevec(b), db._get_wirevec(y)
        alo, ahi = awv[:16], awv[16:]
        blo, bhi = bwv[:16], bwv[16:]
        # p0 = a_lo * b_lo
        cur = db.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(blo)))
        row = cur.fetchone()
        if row is None:
            p0 = [db.auto_id for _ in range(32)]
            p0 = db._create_or_lookup_wirevec(p0)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(blo), p0))
        else:
            p0 = row[0]
        # p2 = a_hi * b_hi
        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(ahi), db._create_or_lookup_wirevec(bhi)))
        row = cur.fetchone()
        if row is None:
            p2 = [db.auto_id for _ in range(32)]
            p2 = db._create_or_lookup_wirevec(p2)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (db._create_or_lookup_wirevec(ahi), db._create_or_lookup_wirevec(bhi), p2))
        else:
            p2 = row[0]
        # a_lo + a_hi
        cur.execute("SELECT y FROM aby_cells WHERE type = '$adds' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(ahi)))
        row = cur.fetchone()
        if row is None:
            a_lo_plus_a_hi = [db.auto_id for _ in range(17)]
            a_lo_plus_a_hi = db._create_or_lookup_wirevec(a_lo_plus_a_hi)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(ahi), a_lo_plus_a_hi))
        else:
            a_lo_plus_a_hi = row[0]
        # b_lo + b_hi
        cur.execute("SELECT y FROM aby_cells WHERE type = '$adds' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(blo), db._create_or_lookup_wirevec(bhi)))
        row = cur.fetchone()
        if row is None:
            b_lo_plus_b_hi = [db.auto_id for _ in range(17)]
            b_lo_plus_b_hi = db._create_or_lookup_wirevec(b_lo_plus_b_hi)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (db._create_or_lookup_wirevec(blo), db._create_or_lookup_wirevec(bhi), b_lo_plus_b_hi))
        else:
            b_lo_plus_b_hi = row[0]
        # p1 = (a_lo + a_hi) * (b_lo + b_hi)
        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (a_lo_plus_a_hi, b_lo_plus_b_hi))
        row = cur.fetchone()
        if row is None:
            p1 = [db.auto_id for _ in range(34)]
            p1 = db._create_or_lookup_wirevec(p1)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (a_lo_plus_a_hi, b_lo_plus_b_hi, p1))
        else:
            p1 = row[0]
        # p1 - p0
        cur.execute("SELECT y FROM aby_cells WHERE type = '$subs' AND a = %s AND b = %s", (p1, p0))
        row = cur.fetchone()
        if row is None:
            p1_sub_p0 = [db.auto_id for _ in range(34)]
            p1_sub_p0 = db._create_or_lookup_wirevec(p1_sub_p0)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$subs', %s, %s, %s)", (p1, p0, p1_sub_p0))
        else:
            p1_sub_p0 = row[0]
        # p1 - p0 - p2
        cur.execute("SELECT y FROM aby_cells WHERE type = '$subs' AND a = %s AND b = %s", (p1_sub_p0, p2))
        row = cur.fetchone()
        if row is None:
            mid = [db.auto_id for _ in range(34)]
            mid = db._create_or_lookup_wirevec(mid)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$subs', %s, %s, %s)", (p1_sub_p0, p2, mid))
        else:
            mid = row[0]
        # (p1 - p0 - p2) << 16
        mid_shift = db._create_or_lookup_wirevec([0 for _ in range(16)] + db._get_wirevec(mid))
        # p2 << 32
        p2_shift = db._create_or_lookup_wirevec([0 for _ in range(32)] + db._get_wirevec(p2))
        # p0 + ((p1 - p0 - p2) << 16)
        cur.execute("SELECT y FROM aby_cells WHERE type = '$adds' AND a = %s AND b = %s", (p0, mid_shift))
        row = cur.fetchone()
        if row is None:
            low_part = [db.auto_id for _ in range(64)]
            low_part = db._create_or_lookup_wirevec(low_part)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (p0, mid_shift, low_part))
        else:
            low_part = row[0]
        # y = p0 + ((p1 - p0 - p2) << 16) + (p2 << 32)
        cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (low_part, p2_shift, y))
        cnt += cur.rowcount > 0
    db.commit()
    return cnt


def apply_wide_muls_split_v2(db: NetlistDB, matches: Iterable[tuple[int, int, int]], a_width: int = 32, b_width: int = 32, y_width: int = 64) -> int:
    """
    p0 = a_lo * b_lo
    p1 = a_lo * b_hi
    p2 = a_hi * b_lo
    p3 = a_hi * b_hi
    y = p0 + (p1 << 16) + (p2 << 16) + (p3 << 32)
    """
    assert a_width == 32 and b_width == 32 and y_width == 64, "Currently only support 32-bit wide muls"
    cnt = 0
    for a, b, y in matches:
        awv, bwv, ywv = db._get_wirevec(a), db._get_wirevec(b), db._get_wirevec(y)
        alo, ahi = awv[:16], awv[16:]
        blo, bhi = bwv[:16], bwv[16:]
        # p0 = a_lo * b_lo
        cur = db.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(blo)))
        row = cur.fetchone()
        if row is None:
            p0 = [db.auto_id for _ in range(32)]
            p0 = db._create_or_lookup_wirevec(p0)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(blo), p0))
        else:
            p0 = row[0]
        # p1 = a_lo * b_hi
        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(bhi)))
        row = cur.fetchone()
        if row is None:
            p1 = [db.auto_id for _ in range(32)]
            p1 = db._create_or_lookup_wirevec(p1)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (db._create_or_lookup_wirevec(alo), db._create_or_lookup_wirevec(bhi), p1))
        else:
            p1 = row[0]
        # p2 = a_hi * b_lo
        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(ahi), db._create_or_lookup_wirevec(blo)))
        row = cur.fetchone()
        if row is None:
            p2 = [db.auto_id for _ in range(32)]
            p2 = db._create_or_lookup_wirevec(p2)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (db._create_or_lookup_wirevec(ahi), db._create_or_lookup_wirevec(blo), p2))
        else:
            p2 = row[0]
        # p3 = a_hi * b_hi
        cur.execute("SELECT y FROM aby_cells WHERE type = '$muls' AND a = %s AND b = %s", (db._create_or_lookup_wirevec(ahi), db._create_or_lookup_wirevec(bhi)))
        row = cur.fetchone()
        if row is None:
            p3 = [db.auto_id for _ in range(32)]
            p3 = db._create_or_lookup_wirevec(p3)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$muls', %s, %s, %s)", (db._create_or_lookup_wirevec(ahi), db._create_or_lookup_wirevec(bhi), p3))
        else:
            p3 = row[0]
        # p1 << 16
        p1_shift = db._create_or_lookup_wirevec([0 for _ in range(16)] + db._get_wirevec(p1))
        # p2 << 16
        p2_shift = db._create_or_lookup_wirevec([0 for _ in range(16)] + db._get_wirevec(p2))
        # p3 << 32
        p3_shift = db._create_or_lookup_wirevec([0 for _ in range(32)] + db._get_wirevec(p3))
        # p0 + (p1 << 16)
        cur.execute("SELECT y FROM aby_cells WHERE type = '$adds' AND a = %s AND b = %s", (p0, p1_shift))
        row = cur.fetchone()
        if row is None:
            part1 = [db.auto_id for _ in range(64)]
            part1 = db._create_or_lookup_wirevec(part1)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (p0, p1_shift, part1))
        else:
            part1 = row[0]
        # p0 + (p1 << 16) + (p2 << 16)
        cur.execute("SELECT y FROM aby_cells WHERE type = '$adds' AND a = %s AND b = %s", (part1, p2_shift))
        row = cur.fetchone()
        if row is None:
            part2 = [db.auto_id for _ in range(64)]
            part2 = db._create_or_lookup_wirevec(part2)
            db.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (part1, p2_shift, part2))
        else:
            part2 = row[0]
        # y = p0 + (p1 << 16) + (p2 << 16) + (p3 << 32)
        cur.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$adds', %s, %s, %s)", (part2, p3_shift, y))
        cnt += cur.rowcount > 0
    db.commit()
    return cnt