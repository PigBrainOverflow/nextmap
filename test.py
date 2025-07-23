from typing import Callable
import os
import subprocess
import json
from emap import *


YOSYS_PATH = "/usr/local/bin/yosys" # replace with your Yosys path

"""
Utility Functions
"""
def synth_verilog(infile: str, outfile: str):
    # just call `proc` command
    res = subprocess.run([YOSYS_PATH, "-p", f"read_verilog -sv {infile}; proc; write_json {outfile}"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Yosys synthesis failed: {res.stderr}")

def import_design(design_path: str, top: str = "top") -> NetlistDB:
    db = NetlistDB("emap/schema.sql", ":memory:", cnt=1000000)
    with open(design_path, "r") as f:
        mod = json.load(f)
    db.build_from_json(mod["modules"][top])
    return db

"""
Unit Tests for Handcrafted Designs
"""
def test_dot_product(dsp_rules: list, cost_model: Callable):
    print("Testing dot product...")
    db = import_design("./tests/out/handcrafted/dot_product_orignal.json")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    rewrites.rewrite_dff_backward_aby_cell(db, ["$adds", "$muls"])
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=2, cost_model=cost_model)
    with open("./tests/out/handcrafted/dot_product.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

def test_complex_multiplier(dsp_rules: list, cost_model: Callable):
    print("Testing complex multiplier...")
    db = import_design("./tests/out/handcrafted/complex_multiplier_orignal.json")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    rewrites.rewrite_complex_mul(db)    # TODO: Can we provide more generic rewrites?
    while rewrites.rewrite_dff_backward_aby_cell(db, ["$adds", "$subs", "$muls"]) > 0:
        pass
    rewrites.rewrite_comm(db, ["$adds", "$muls"])
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=3, cost_model=cost_model)
    with open("./tests/out/handcrafted/complex_multiplier.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

def test_square_diff(dsp_rules: list, cost_model: Callable):
    print("Testing square diff...")
    db = import_design("./tests/out/handcrafted/square_diff_orignal.json")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    while rewrites.rewrite_dff_backward_aby_cell(db, ["$subs", "$muls"]) > 0:
        pass
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=1, cost_model=cost_model)
    with open("./tests/out/handcrafted/square_diff.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

def test_signed_mac(dsp_rules: list, cost_model: Callable):
    print("Testing signed MAC...")
    db = import_design("./tests/out/handcrafted/signed_mac_orignal.json")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    while rewrites.rewrite_dff_backward_aby_cell(db, ["$adds", "$muls"]) > 0:
        pass
    rewrites.rewrite_comm(db, ["$adds", "$muls"])
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=1, cost_model=cost_model)
    with open("./tests/out/handcrafted/signed_mac.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

def test_unsigned_mac(dsp_rules: list, cost_model: Callable):
    print("Testing unsigned MAC...")
    db = import_design("./tests/out/handcrafted/unsigned_mac_orignal.json")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    while rewrites.rewrite_dff_backward_aby_cell(db, ["$addu", "$mulu"]) > 0:
        pass
    rewrites.rewrite_comm(db, ["$addu", "$mulu"])
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=1, cost_model=cost_model)
    with open("./tests/out/handcrafted/unsigned_mac.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

def test_wide_multiplier(dsp_rules: list, cost_model: Callable):
    print("Testing wide multiplier...")
    db = import_design("./tests/out/handcrafted/wide_multiplier_orignal.json")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    rewrites.rewrite_split_wide_mul(db, a_width=17, b_width=26)   # maximum width of unsigned multiplication
    rewrites.rewrite_split_wide_dff(db, width=17)
    while rewrites.rewrite_dff_backward_aby_cell(db, ["$addu", "$mulu"]) > 0:
        pass
    # rewrites.rewrite_comm(db, ["$addu", "$mulu"])
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    with open("out.json", "w") as f:
        json.dump(db.dump_tables(), f, indent=2)
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=1, cost_model=cost_model)
    with open("./tests/out/handcrafted/wide_multiplier.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

def test_handcrafted_all(synth: bool = False):
    # NOTE: all designs only have one module named "top"
    design_path = "./tests/designs/handcrafted"
    out_path = "./tests/out/handcrafted"
    dsp_rule_path = "./tests/rulesets/xilinx-xcup/dsp.json"

    # preprocess
    if synth:
        for file in os.listdir(design_path):
            if file.endswith(".v") or file.endswith(".sv"):
                infile = os.path.join(design_path, file)
                outfile = os.path.join(out_path, f"{os.path.splitext(file)[0]}_orignal.json")
                print(f"Synthesizing {infile} to {outfile}")
                synth_verilog(infile, outfile)

    with open(dsp_rule_path, "r") as f:
        dsp_rules = json.load(f)

    def simple_cost_model(x: tuple) -> float:
        if x[0] in {"$muls", "$mulu"}:
            return NetlistDB.width_of(x[1]) * NetlistDB.width_of(x[2]) * 1.0
        elif x[0] == "$dff":
            return NetlistDB.width_of(x[1]) * 0.5
        else:
            return NetlistDB.width_of(x[1]) + NetlistDB.width_of(x[2]) * 1.0

    # run tests
    test_dot_product(dsp_rules, simple_cost_model)
    test_complex_multiplier(dsp_rules, simple_cost_model)
    test_square_diff(dsp_rules, simple_cost_model)
    test_signed_mac(dsp_rules, simple_cost_model)
    test_unsigned_mac(dsp_rules, simple_cost_model)
    test_wide_multiplier(dsp_rules, simple_cost_model)

def test_systolic():
    dsp_rule_path = "./tests/rulesets/xilinx-xcup/dsp.json"
    with open(dsp_rule_path, "r") as f:
        dsp_rules = json.load(f)
    # no need to synthesize
    def simple_cost_model(x: tuple) -> float:
        if x[0] in {"$muls", "$mulu"}:
            return NetlistDB.width_of(x[1]) * NetlistDB.width_of(x[2]) * 1.0
        elif x[0] == "$dff":
            return NetlistDB.width_of(x[1]) * 0.5
        else:
            return NetlistDB.width_of(x[1]) + NetlistDB.width_of(x[2]) * 1.0

    print("Testing Systolic...")
    db = import_design("./tests/designs/systolic/systolic.json", top="systolic")
    rewrites.create_dsp_tables(db, dsp_rules)
    # rewrite
    while rewrites.rewrite_dff_backward_aby_cell(db, ["$adds", "$addu", "$subs", "$subu", "$muls", "$mulu"]) > 0:
        pass
    rewrites.rewrite_comm(db, ["$adds", "$addu", "$subs", "$subu", "$muls", "$mulu"])
    [rewrites.rewrite_dsp(db, rule) for rule in dsp_rules]
    with open("out.json", "w") as f:
        json.dump(db.dump_tables(), f, indent=2)
    # extract
    design = extracts.ilp.extract_dsps_by_count(db, "dsp48e2", count=1024, cost_model=simple_cost_model)
    # design = extracts.ilp.extract_dsps_by_cost(db, "dsp48e2", cost_model=simple_cost_model)
    with open("./tests/out/systolic/systolic.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": design}}, f, indent=2)

if __name__ == "__main__":
    # test_handcrafted_all()
    test_systolic()

    print("All tests completed successfully.")