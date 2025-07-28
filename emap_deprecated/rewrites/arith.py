from ..db import NetlistDB


"""
more advanced rewrites for arithmetic cells
disabled by default
"""

def rewrite_complex_mul(db: NetlistDB, subsume: bool = False) -> int:
    assert not subsume, "Subsumption is not supported for complex multiplication rewrites"

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

    cnt = 0
    for a, b, c, d, y1, y2 in cur.fetchall():
        a_sub_b = db.find_or_create_aby_cell(NetlistDB.width_of(a), "$subs", a, b)
        factor = db.find_or_create_aby_cell(NetlistDB.width_of(y1), "$muls", a_sub_b, d)
        c_sub_d = db.find_or_create_aby_cell(NetlistDB.width_of(c), "$subs", c, d)
        factor1 = db.find_or_create_aby_cell(NetlistDB.width_of(y1), "$muls", c_sub_d, a)
        c_add_d = db.find_or_create_aby_cell(NetlistDB.width_of(c), "$adds", c, d)
        factor2 = db.find_or_create_aby_cell(NetlistDB.width_of(y2), "$muls", c_add_d, b)
        cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", ("$adds", factor, factor1, y1))
        cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", ("$adds", factor, factor2, y2))
        cnt += cur.rowcount > 0

    db.commit()
    return cnt

def rewrite_split_wide_mul(db: NetlistDB, a_width: int, b_width: int, subsume: bool = False) -> int:
    assert not subsume, "Subsumption is not supported for wide multiplication rewrites"
    # for simplicity, we only rewrite unsigned multiplication
    # each time it splits `b` into two parts if the width of `b` is larger than `b_width`
    # and the width of `a` is no larger than `a_width`

    cur = db.execute("SELECT a, b, y FROM aby_cells WHERE type = '$mulu' AND width_of(a) <= ? AND width_of(b) > ? AND width_of(y) > ?", (a_width, b_width, b_width))

    cnt = 0
    for a, b, y in cur.fetchall():
        bs, ys = b.split(","), y.split(",")
        blo, bhi = bs[:a_width], bs[a_width:]
        ylo, yhi = ys[:a_width], ys[a_width:]
        a_blo = db.next_wires(len(ys) - a_width)+ "," + ",".join(ylo)
        cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", ("$mulu", a, ",".join(blo), a_blo))
        a_bhi = db.find_or_create_aby_cell(len(ys) - a_width, "$mulu", a, ",".join(bhi))
        cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", ("$addu", a_bhi, a_blo, ",".join(yhi)))
        cnt += cur.rowcount > 0

    db.commit()
    return cnt