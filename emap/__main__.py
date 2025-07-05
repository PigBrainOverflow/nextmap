from emap.db import NetlistDB
import argparse
import json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", nargs="?", type=str, default="emap/schema.sql", help="Path to the schema file")
    parser.add_argument("--db", nargs="?", type=str, default=":memory:", help="Path to the database file")
    parser.add_argument("--json", type=str, help="Path to the JSON file")
    parser.add_argument("--top", type=str, help="Name of the top module")
    args = parser.parse_args()
    db = NetlistDB(schema_file=args.schema, db_file=args.db)

    with open(args.json, "r") as f:
        mod = json.load(f)

    db.build_from_json(mod["modules"][args.top])
    cur = db.execute("SELECT * FROM aby_cells")
    for type_, a, b, y in cur:
        print(f"Cell: {type_}, A: {a}, B: {b}, Y: {y}")
