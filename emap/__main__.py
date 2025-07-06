from emap import NetlistDB
from emap.rewrites import *
import argparse
import json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", nargs="?", type=str, default="emap/schema.sql", help="Path to the schema file")
    parser.add_argument("--db", nargs="?", type=str, default=":memory:", help="Path to the database file")
    parser.add_argument("--design", type=str, help="Path to the design JSON file")
    parser.add_argument("--top", type=str, help="Name of the top module")
    parser.add_argument("--rules", type=str, help="Path to the directory of ruleset files")
    args = parser.parse_args()
    db = NetlistDB(schema_file=args.schema, db_file=args.db)

    with open(args.design, "r") as f:
        mod = json.load(f)

    db.build_from_json(mod["modules"][args.top])

    rewrite_comm(db, ["$adds", "$addu", "$muls", "$mulu"])
    rewrite_assoc_to_right(db, ["$adds", "$addu", "$muls", "$mulu"])
    rewrite_dff_forward_aby_cell(db, ["$adds", "$addu", "$muls", "$mulu"])

    with open("out.json", "w") as f:
        json.dump(db.dump_tables(), f, indent=2)