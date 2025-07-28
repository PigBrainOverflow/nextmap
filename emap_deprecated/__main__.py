from emap import NetlistDB
from emap.rewrites import *
from emap.extracts import greedy, ilp
import argparse
import json


def test_greedy_extract_dsps(db: NetlistDB, top: str):
    # use no more than 2 DSPs
    # NOTE: call `clean -purge` in yosys
    greedy.fix_dsps(db, "dsp48e2", 2)
    new_design = greedy.extract_dsps_bottom_up(db, "dsp48e2", cost_model=lambda x: 10 if x[0] == "$muls" else 1)
    with open("out_greedy.json", "w") as f:
        json.dump(
            {"creator": "nextmap", "modules": {top: new_design}},
            f, indent=2
        )

def test_ilp_extract_dsps_by_count(db: NetlistDB, top: str):
    # extract DSPs by a fixed count
    def cost_model(x: tuple) -> float:
        if x[0] == "$muls":
            return NetlistDB.width_of(x[1]) * NetlistDB.width_of(x[2]) * 1.0
        elif x[0] == "$dff":
            return NetlistDB.width_of(x[1]) * 0.5
        else:
            return NetlistDB.width_of(x[1]) + NetlistDB.width_of(x[2]) * 1.0
    new_design = ilp.extract_dsps_by_count(db, "dsp48e2", count=3, cost_model=cost_model)
    with open("out_ilp_count.json", "w") as f:
        json.dump(
            {"creator": "nextmap", "modules": {top: new_design}},
            f, indent=2
        )

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

    # rewrite_complex_mul(db)
    # while rewrite_dff_backward_aby_cell(db, ["$adds", "$subs", "$muls"]) > 0:
    #     pass
    # rewrite_comm(db, ["$adds", "$muls"])

    # for rule in dsp_rules:
    #     rewrite_dsp(db, rule)

    with open("out_rewrite.json", "w") as f:
        json.dump(db.dump_tables(), f, indent=2)

    # test_greedy_extract_dsps(db, args.top)
    test_ilp_extract_dsps_by_count(db, args.top)