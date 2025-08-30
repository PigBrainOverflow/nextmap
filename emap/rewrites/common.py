from typing import Iterable
from ..db import NetlistDB


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