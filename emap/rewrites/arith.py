from ..db import NetlistDB


"""
more advanced rewrites for arithmetic cells
disabled by default
"""

def rewrite_complex_mul(db: NetlistDB, subsume: bool = False) -> bool:
    # return True if any rewrites were made, False otherwise
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
        LIMIT 1
    """)

    row = cur.fetchone()
    if row is None:
        return False
    a, b, c, d, y1, y2 = row
    a_sub_b = db.find_or_create_aby_cell(NetlistDB.width_of(a), "$subs", a, b)
    factor = db.find_or_create_aby_cell(NetlistDB.width_of(y1), "$muls", a_sub_b, d)
    c_sub_d = db.find_or_create_aby_cell(NetlistDB.width_of(c), "$subs", c, d)
    factor1 = db.find_or_create_aby_cell(NetlistDB.width_of(y1), "$muls", c_sub_d, a)
    c_add_d = db.find_or_create_aby_cell(NetlistDB.width_of(c), "$adds", c, d)
    factor2 = db.find_or_create_aby_cell(NetlistDB.width_of(y2), "$muls", c_add_d, b)
    cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", ("$adds", factor, factor1, y1))
    cur.execute("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", ("$adds", factor, factor2, y2))
    db.commit()

    return cur.rowcount > 0