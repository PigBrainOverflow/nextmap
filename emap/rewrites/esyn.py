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


def ematch_aby_idemp(netlist: NetlistDB, types: list[str] = ["$and", "$or"]) -> list[tuple[str, int, int]]:
    """
    (op ?x ?x) => ?x
    """
    cur = netlist.execute(f"SELECT type, a, y FROM aby_cells WHERE type IN ({','.join(['?']*len(types))}) AND a = b", types)
    return cur.fetchall()

def apply_aby_idemp(matches: list[tuple[str, int, int]], wdsu: DisjointSetUnion) -> int:
    for _, a, y in matches:
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