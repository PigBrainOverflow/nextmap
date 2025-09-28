from ..db import NetlistDB
from typing import Any


def create_tech_tables(db: NetlistDB, rules: dict[str, dict[str, Any]]):
    for name, rule in rules.items():
        db.execute("CREATE TABLE IF NOT EXISTS tech_{} ({}, PRIMARY KEY({}));".format(
            name,
            ",".join(f"{port} INTEGER" for port in (rule["inputs"] + rule["outputs"])),
            ",".join(rule["inputs"])
        ))

def rewrite_tech(db: NetlistDB, rules: dict[str, dict[str, Any]]) -> int:
    cnt = 0
    for name, rule in rules.items():
        try:
            cur = db.execute("INSERT OR IGNORE INTO {} {}".format(f"tech_{name}", rule["match_sql"]))
            db.commit()
            cnt += cur.rowcount
        except Exception as e:
            print(f"Error techmapping {name}: {e}. Skipping.")
    return cnt