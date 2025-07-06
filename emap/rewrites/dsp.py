from ..db import NetlistDB


"""
dsp proposal rewrites
"""

def create_dsp_tables(db: NetlistDB, rules: list[dict]):
    """
    Create tables for DSP proposals in the database.
    """
    for rule in rules:
        db.execute("CREATE TABLE IF NOT EXISTS {} (value INTEGER, {}, PRIMARY KEY ({}));".format(
            rule["name"],
            ",".join(f"{port['name']} VARCHAR(64)" for port in rule["ports"]),
            ",".join(port["name"] for port in rule["ports"] if port["is_input"])
        ))

def rewrite_dsp(db: NetlistDB, rule: dict, subsume: bool = False) -> int:
    assert not subsume, "DSP rewrites do not support subsumption yet"

    cur = db.execute("INSERT OR IGNORE INTO {} {}".format(rule["name"], rule["match_sql"]))
    return cur.rowcount