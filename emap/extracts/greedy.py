from ..db import NetlistDB


def _delete_subset_rows(db: NetlistDB, table: str, output: str, wires: set[str]):
    """
    Delete rows in the specified table where the output wires are a subset of the given wires.
    """
    # this is a helper function to delete rows in the same eclass
    # costly since it requires a full scan of the table
    cur = db.execute(f"SELECT rowid, {output} FROM {table}")
    for row in cur.fetchall():
        if set(row[1].split(",")) <= wires:
            db.execute(f"DELETE FROM {table} WHERE rowid = ?", (row[0],))

def greedy_fix_one_dsp(db: NetlistDB, name: str) -> int:
    # return the value of the fixed dsp
    # this is a kind of heuristic
    tables = db.tables_startswith(name)

    # for each table, find the row with largest value
    largest = (0, None, None)   # (value, row, table)
    for table in tables:
        cur = db.execute(f"SELECT rowid, * FROM {table} ORDER BY value DESC LIMIT 1")
        row = cur.fetchone()
        if row is not None and row[1] > largest[0]:
            largest = (row[1], row, table)

    if largest[0] > 0 and largest[1] is not None:
        _, row, table = largest
        # first, remove all rows with the same or subset output (in the same eclass)
        # suppose `output` is in the last column
        output_wires = set(row[-1].split(","))
        _delete_subset_rows(db, "aby_cells", "y", output_wires)
        _delete_subset_rows(db, "dffs", "q", output_wires)
        for table_ in tables:
            _delete_subset_rows(db, table_, "out", output_wires)
        # then, insert the row with value 0
        db.execute(f"INSERT INTO {table} VALUES ({','.join(['?'] * (len(row) - 1))})", (0, *row[2:]))
        db.commit()

    return largest[0]
