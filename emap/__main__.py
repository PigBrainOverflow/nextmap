from emap import NetlistDB
from emap.rewrites import *
from emap.extracts import greedy, ilp
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
    db = NetlistDB(schema_file=args.schema, db_file=args.db, cnt=1000)

    with open(args.design, "r") as f:
        mod = json.load(f)

    with open(f"{args.rules}/dsp.json", "r") as f:
        dsp_rules = json.load(f)

    create_dsp_tables(db, dsp_rules)
    db.build_from_json(mod["modules"][args.top])

    # rewrite_dff_forward_aby_cell(db, ["$adds", "$addu", "$muls", "$mulu"])
    # rewrite_dff_forward_aby_cell(db, ["$adds", "$addu", "$muls", "$mulu"])
    # rewrite_comm(db, ["$adds", "$addu", "$muls", "$mulu"])
    # rewrite_assoc_to_right(db, ["$adds", "$addu", "$muls", "$mulu"])
    rewrite_complex_mul(db)
    rewrite_dff_backward_aby_cell(db, ["$adds", "$addu", "$subs", "$subu", "$muls", "$mulu"])

    print(rewrite_dsp(db, dsp_rules[-2]))

    greedy.fix_dsps(db, "dsp48e2", 2)
    # new_design = greedy.extract_dsps_bottom_up(
    #     db,
    #     "dsp48e2",
    #     cost_model=lambda x: 100 if x[0] == "$muls" else 1
    # )
    new_design = ilp.extract_dsps(
        db,
        "dsp48e2",
        cost_model=lambda x: 100 if x[0] == "$muls" else 1
    )

    with open("out.json", "w") as f:
        json.dump(db.dump_tables(), f, indent=2)

    with open("out_design.json", "w") as f:
        json.dump(
            {"creator": "nextmap", "modules": {args.top: new_design}},
            f, indent=2
        )