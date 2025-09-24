from ..db import NetlistDB
from ..utils import DisjointSetUnion


def ematch_not_idemp(netlist: NetlistDB) -> list[tuple[int, int]]:
    """
    (! (! ?x)) => ?x
    """
    cur = netlist.execute("SELECT not1.a, not2.y FROM ay_cells AS not1 JOIN ay_cells AS not2 ON not1.y = not2.a WHERE not1.type = '$not' AND not2.type = '$not' AND not1.a != not2.y")
    return cur.fetchall()

def apply_not_idemp(matches: list[tuple[int, int]], wdsu: DisjointSetUnion) -> int:
    for a1, y2 in matches:
        wdsu.union(a1, y2)
    return len(matches)


def ematch_aby_idemp(netlist: NetlistDB, types: list[str] = ["$and", "$or"]) -> list[tuple[int, int]]:
    """
    (op ?x ?x) => ?x
    """
    cur = netlist.execute(f"SELECT a, y FROM aby_cells WHERE type IN ({','.join(['?']*len(types))}) AND a = b AND a != y", types)
    return cur.fetchall()

def apply_aby_idemp(matches: list[tuple[int, int]], wdsu: DisjointSetUnion) -> int:
    for a, y in matches:
        wdsu.union(a, y)
    return len(matches)


def ematch_aby_assoc_left(netlist: NetlistDB, types: list[str] = ["$and", "$or"]) -> list[tuple[str, int, int, int, int]]:
    """
    (op (op ?x ?y) ?z) => (op ?x (op ?y ?z))
    """
    cur = netlist.execute(f"""
        SELECT c1.type, c1.a, c1.b, c2.b, c2.y
        FROM aby_cells AS c1 JOIN aby_cells AS c2
        ON c1.type = c2.type AND c1.y = c2.a
        WHERE c1.type IN ({','.join(['?']*len(types))})
    """, types)
    return cur.fetchall()

def apply_aby_assoc_left(netlist: NetlistDB, matches: list[tuple[str, int, int, int, int]]) -> int:
    newrows = []
    for type_, a, b, c, y in matches:
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = ? AND a = ? AND b = ?", (type_, b, c))
        row = cur.fetchone()
        if row is None:
            bc = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", (type_, b, c, bc))
        else:
            bc = row[0]
        newrows.append((type_, a, bc, y))
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    netlist.commit()
    return cur.rowcount


# TODO: I don't know why no assoc_right is not needed


def ematch_aby_comm(netlist: NetlistDB, types: list[str] = ["$and", "$or"]) -> list[tuple[str, int, int, int]]:
    """
    (op ?x ?y) => (op ?y ?x)
    """
    cur = netlist.execute(f"""
        SELECT type, a, b, y
        FROM aby_cells
        WHERE type IN ({','.join(['?']*len(types))})
    """, types)
    return cur.fetchall()

def apply_aby_comm(netlist: NetlistDB, matches: list[tuple[str, int, int, int]]) -> int:
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", [(type_, b, a, y) for (type_, a, b, y) in matches])
    netlist.commit()
    return cur.rowcount


def ematch_andor_distrib(netlist: NetlistDB) -> list[tuple[int, int, int, int]]:
    """
    (and ?x (or ?y ?z)) => (or (and ?x ?y) (and ?x ?z))
    """
    cur = netlist.execute("""
        SELECT and1.a, or1.a, or1.b, and1.y
        FROM aby_cells AS and1 JOIN aby_cells AS or1
        ON and1.b = or1.y
        WHERE and1.type = '$and' AND or1.type = '$or'
    """)
    return cur.fetchall()

def apply_andor_distrib(netlist: NetlistDB, matches: list[tuple[int, int, int, int]]) -> int:
    newrows = []
    for a, b, c, y in matches:
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = ? AND b = ?", (a, b))
        row = cur.fetchone()
        if row is None:
            ab = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", (a, b, ab))
        else:
            ab = row[0]
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = ? AND b = ?", (a, c))
        row = cur.fetchone()
        if row is None:
            ac = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", (a, c, ac))
        else:
            ac = row[0]
        newrows.append(("$or", ab, ac, y))
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    netlist.commit()
    return cur.rowcount


def ematch_orand_distrib(netlist: NetlistDB) -> list[tuple[int, int, int, int]]:
    """
    (or ?x (and ?y ?z)) => (and (or ?x ?y) (or ?x ?z))
    """
    cur = netlist.execute("""
        SELECT or1.a, and1.a, and1.b, or1.y
        FROM aby_cells AS or1 JOIN aby_cells AS and1
        ON or1.b = and1.y
        WHERE or1.type = '$or' AND and1.type = '$and'
    """)
    return cur.fetchall()

def apply_orand_distrib(netlist: NetlistDB, matches: list[tuple[int, int, int, int]]) -> int:
    newrows = []
    for a, b, c, y in matches:
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$or' AND a = ? AND b = ?", (a, b))
        row = cur.fetchone()
        if row is None:
            ab = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$or', ?, ?, ?)", (a, b, ab))
        else:
            ab = row[0]
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$or' AND a = ? AND b = ?", (a, c))
        row = cur.fetchone()
        if row is None:
            ac = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$or', ?, ?, ?)", (a, c, ac))
        else:
            ac = row[0]
        newrows.append(("$and", ab, ac, y))
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    netlist.commit()
    return cur.rowcount


def ematch_absorp(netlist: NetlistDB) -> list[tuple[int, int]]:
    """
    (or ?x (and ?x ?y)) => ?x
    """
    cur = netlist.execute("""
        SELECT or1.a, or1.y
        FROM aby_cells AS or1 JOIN aby_cells AS and1
        ON or1.a = and1.a
        WHERE or1.type = '$or' AND and1.type = '$and' AND or1.a != or1.y
    """)
    return cur.fetchall()

def apply_absorp(matches: list[tuple[int, int]], wdsu: DisjointSetUnion) -> int:
    for a, y in matches:
        wdsu.union(a, y)
    return len(matches)


def ematch_th11(netlist: NetlistDB) -> list[tuple[int, int, int]]:
    """
    (or ?x (and (! ?x) ?y)) => (or ?x ?y)
    """
    cur = netlist.execute("""
        SELECT or1.a, and1.b, or1.y
        FROM aby_cells AS or1 JOIN aby_cells AS and1 JOIN ay_cells AS not1
        ON or1.b = and1.y AND not1.y = and1.a AND or1.a = not1.a
        WHERE or1.type = '$or' AND and1.type = '$and' AND not1.type = '$not'
    """)
    return cur.fetchall()

def apply_th11(netlist: NetlistDB, matches: list[tuple[int, int, int]]) -> int:
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES ('$or', ?, ?, ?)", matches)
    netlist.commit()
    return cur.rowcount


def ematch_th13(netlist: NetlistDB) -> list[tuple[int, int]]:
    """
    (and ?x (or ?x ?y)) => ?x
    """
    cur = netlist.execute("""
        SELECT and1.a, and1.y
        FROM aby_cells AS and1 JOIN aby_cells AS or1
        ON and1.b = or1.y
        WHERE and1.type = '$and' AND or1.type = '$or' AND and1.a != and1.y
    """)
    return cur.fetchall()

def apply_th13(matches: list[tuple[int, int]], wdsu: DisjointSetUnion) -> int:
    for a, y in matches:
        wdsu.union(a, y)
    return len(matches)


def ematch_th14(netlist: NetlistDB) -> list[tuple[int, int, int]]:
    """
    (and ?x (or (! ?x) ?y)) => (and ?x ?y)
    """
    cur = netlist.execute("""
        SELECT and1.a, or1.b, and1.y
        FROM aby_cells AS and1 JOIN aby_cells AS or1 JOIN ay_cells AS not1
        ON and1.b = or1.y AND not1.y = or1.a AND and1.a = not1.a
        WHERE and1.type = '$and' AND or1.type = '$or' AND not1.type = '$not'
    """)
    return cur.fetchall()

def apply_th14(netlist: NetlistDB, matches: list[tuple[int, int, int]]) -> int:
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", matches)
    netlist.commit()
    return cur.rowcount


def ematch_th15(netlist: NetlistDB) -> list[tuple[int, int]]:
    """
    (and (or ?x ?y) (or ?x (! ?y))) => ?x
    """
    cur = netlist.execute("""
        SELECT or1.a, and1.y
        FROM aby_cells AS and1 JOIN aby_cells AS or1 JOIN aby_cells AS or2 JOIN ay_cells AS not1
        ON and1.a = or1.y AND and1.b = or2.y AND or1.a = or2.a AND not1.y = or2.b AND or1.b = not1.a
        WHERE and1.type = '$and' AND or1.type = '$or' AND or2.type = '$or' AND not1.type = '$not' AND or1.a != and1.y
    """)
    return cur.fetchall()

def apply_th15(matches: list[tuple[int, int]], wdsu: DisjointSetUnion) -> int:
    for a, y in matches:
        wdsu.union(a, y)
    return len(matches)


def ematch_th16(netlist: NetlistDB) -> list[tuple[int, int, int, int]]:
    """
    (and (or ?x ?y) (or (! ?x) ?z)) => (or (and ?x ?z) (and (! ?x) ?y))
    """
    cur = netlist.execute("""
        SELECT or1.a, or1.b, or2.b, and1.y
        FROM aby_cells AS and1 JOIN aby_cells AS or1 JOIN aby_cells AS or2 JOIN ay_cells AS not1
        ON and1.a = or1.y AND and1.b = or2.y AND or1.a = not1.a AND not1.y = or2.a
        WHERE and1.type = '$and' AND or1.type = '$or' AND or2.type = '$or' AND not1.type = '$not'
    """)
    return cur.fetchall()

def apply_th16(netlist: NetlistDB, matches: list[tuple[int, int, int, int]]) -> int:
    newrows = []
    for x, y, z, w in matches:
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = ? AND b = ?", (x, z))
        row = cur.fetchone()
        if row is None:
            xz = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", (x, z, xz))
        else:
            xz = row[0]
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$not' AND a = ?", (x,))
        row = cur.fetchone()
        if row is None:
            nx = netlist.auto_id
            netlist.execute("INSERT INTO ay_cells (type, a, y) VALUES ('$not', ?, ?)", (x, nx))
        else:
            nx = row[0]
        cur = netlist.execute("SELECT y FROM aby_cells WHERE type = '$and' AND a = ? AND b = ?", (nx, y))
        row = cur.fetchone()
        if row is None:
            nxy = netlist.auto_id
            netlist.execute("INSERT INTO aby_cells (type, a, b, y) VALUES ('$and', ?, ?, ?)", (nx, y, nxy))
        else:
            nxy = row[0]
        newrows.append(("$or", xz, nxy, w))
    cur = netlist.executemany("INSERT OR IGNORE INTO aby_cells (type, a, b, y) VALUES (?, ?, ?, ?)", newrows)
    netlist.commit()
    return cur.rowcount