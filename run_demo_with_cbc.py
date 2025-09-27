#!/usr/bin/env python3
"""
Run the demo.ipynb examples with CBC solver
"""

import sys
import os
import json

# Add the current directory to the path (assuming we're in nextmap root)
sys.path.insert(0, os.path.abspath('.'))

import emap

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

def run_retiming_demo():
    """Run the retiming demo exactly as in the notebook"""
    print("=== Retiming Demo (from demo.ipynb) ===")

    # Generate the input file
    print("Generating bad_multiplier.json...")
    os.system("yosys -q -p 'read_verilog tests/bad_multiplier.v; proc; opt_merge; opt_clean; write_json bad_multiplier.json'")

    # Run the nextmap code from the notebook
    TEST_NAME = "bad_multiplier"
    SCHEMA_PATH = "emap/schema.sql"
    netlist = emap.NetlistDB(SCHEMA_PATH)
    with open(f"{TEST_NAME}.json", "r") as f:
        netlist.build_from_json(json.load(f)["modules"]["top"])

    netlist.rebuild()
    cnt = 1
    while cnt > 0:
        dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$addu", "$muls", "$mulu"])

        cnt = emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
        if cnt > 0:
            print(f"Applied {cnt} rewrites")
        else:
            print("No rewrites applied, stopping")
        netlist.rebuild()

    print("Extracting with CBC solver (OutputFlag=False)...")
    mod = emap.extracts.ilp.extract_no_techmap(netlist, simple_cost_model, solver_type="cbc", OutputFlag=False)

    with open(f"{TEST_NAME}_extracted_cbc.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)

    print("Results saved!")

    # Compare with yosys output
    print("\n--- Original design stats ---")
    os.system("yosys -Q -T -p 'read_json bad_multiplier.json; stat'")

    print("\n--- CBC extracted design stats ---")
    os.system("yosys -Q -T -p 'read_json bad_multiplier_extracted_cbc.json; stat'")

def run_techmap_demo():
    """Run the technology mapping demo exactly as in the notebook"""
    print("\n=== Technology Mapping Demo (from demo.ipynb) ===")

    # Generate the input file
    print("Generating dot_product.json...")
    os.system("yosys -q -p 'read_verilog tests/dot_product.v; proc; opt_merge; opt_clean; write_json dot_product.json'")

    # Define cost model for techmap
    def techmap_cost_model(type_: str, *ports) -> float:
        if type_ == "$dff":
            return len(ports[0]) * 1.0
        elif type_ in {"$muls", "$mulu"}:
            return len(ports[0]) * len(ports[1]) * 1.0
        elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
            return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
        elif type_.startswith("$"): # other types
            return len(ports[0]) * 1.0
        return 0.0  # blackboxes or tech cells

    # Define DSP rules exactly from notebook
    dsp_rules = {
        "signed_mul_1_stage_26_17_48_bit": {    # rule name
            "requirements": {                   # resource requirements
                "dsp48e2": 1                    # use one DSP48E2
            },
            "hidden_inputs": ["clk"],   # hidden input ports, e.g., clock
            "inputs": ["a", "b"],       # input ports
            "outputs": ["p"],           # output ports
            # and a match pattern in SQL
            "match_sql": """
                SELECT mul1.a, mul1.b, dff1.q
                FROM dffs AS dff1 JOIN aby_cells AS mul1
                ON dff1.d = mul1.y
                WHERE mul1.type = '$muls'
                    AND width_of(mul1.a) <= 26 AND width_of(mul1.b) <= 17 AND width_of(dff1.q) <= 48
            """
        },
        "signed_muladd_1_stage_27_18_48_bit": {
            "requirements": {
                "dsp48e2": 1
            },
            "hidden_inputs": ["clk"],
            "inputs": ["a", "b", "c"],
            "outputs": ["p"],
            "match_sql": """
                SELECT mul1.a, mul1.b, add1.b, dff1.q
                FROM dffs AS dff1 JOIN aby_cells AS mul1 JOIN aby_cells AS add1
                ON dff1.d = add1.y AND mul1.y = add1.a
                WHERE mul1.type = '$muls' AND add1.type = '$adds'
                    AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(add1.b) <= 48 AND width_of(dff1.q) <= 48
            """
        }
    }

    # Run the nextmap code from the notebook
    TEST_NAME = "dot_product"
    SCHEMA_PATH = "emap/schema.sql"
    netlist = emap.NetlistDB(SCHEMA_PATH)
    with open(f"{TEST_NAME}.json", "r") as f:
        netlist.build_from_json(json.load(f)["modules"]["top"])

    netlist.rebuild()
    cnt = 1
    while cnt > 0:
        comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$addu", "$muls", "$mulu"])
        assoc_to_right_matches = emap.rewrites.ematch_assoc_to_right(netlist, ["$adds", "$addu", "$muls", "$mulu"])
        assoc_to_left_matches = emap.rewrites.ematch_assoc_to_left(netlist, ["$adds", "$addu", "$muls", "$mulu"])
        dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$addu", "$muls", "$mulu"])
        dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$addu", "$muls", "$mulu"])

        cnt = 0
        cnt += emap.rewrites.apply_comm(netlist, comm_matches)
        cnt += emap.rewrites.apply_assoc_to_right(netlist, assoc_to_right_matches)
        cnt += emap.rewrites.apply_assoc_to_left(netlist, assoc_to_left_matches)
        cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
        cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_aby_cell_matches)

        if cnt > 0:
            print(f"Applied {cnt} rewrites")
        else:
            print("No rewrites applied, stopping")
        netlist.rebuild()

    # techmapping
    emap.rewrites.create_tech_tables(netlist, dsp_rules)
    emap.rewrites.rewrite_tech(netlist, dsp_rules)

    print("Extracting with CBC solver (OutputFlag=False)...")
    mod = emap.extracts.ilp.extract_techmap_with_limit(netlist, techmap_cost_model, dsp_rules, {"dsp48e2": 2}, solver_type="cbc", OutputFlag=False)

    with open(f"{TEST_NAME}_extracted_cbc.json", "w") as f:
        json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)

    print("Results saved!")

    # Compare results
    print("\n--- Yosys baseline (with DSP synthesis) ---")
    os.system("yosys -q -p 'read_verilog tests/dot_product.v; synth_xilinx -family xcup; write_json dot_product_xilinx.json'")
    os.system("yosys -Q -T -p 'read_json dot_product_xilinx.json; stat'")

    print("\n--- CBC extracted + Yosys synthesis ---")
    if os.path.exists("tests/dsp_blackboxes.v"):
        os.system("yosys -q -p 'read_verilog tests/dsp_blackboxes.v; read_json dot_product_extracted_cbc.json; synth_xilinx -family xcup; write_json dot_product_nextmap_cbc.json'")
        os.system("yosys -Q -T -p 'read_json dot_product_nextmap_cbc.json; stat'")
    else:
        print("Note: dsp_blackboxes.v not found, showing raw extracted stats")
        os.system("yosys -Q -T -p 'read_json dot_product_extracted_cbc.json; stat'")

def analyze_json_file(filename, title):
    """Analyze a JSON file and print cell statistics"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        cells = data.get("modules", {}).get("top", {}).get("cells", {})

        print(f"\n--- {title} ---")
        print(f"Total cells: {len(cells)}")

        # Count by type
        type_counts = {}
        for cell in cells.values():
            cell_type = cell.get("type", "unknown")
            type_counts[cell_type] = type_counts.get(cell_type, 0) + 1

        for cell_type, count in sorted(type_counts.items()):
            print(f"  {cell_type}: {count}")

    except FileNotFoundError:
        print(f"{filename} not found")
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")

if __name__ == "__main__":
    print("Running demo.ipynb examples with CBC solver...")

    # Change to project directory
    # Assume we're already in the nextmap root directory
    # os.chdir not needed

    run_retiming_demo()
    run_techmap_demo()

    # Analyze the results
    print("\n" + "="*60)
    print("ANALYSIS OF RESULTS")
    print("="*60)

    analyze_json_file("bad_multiplier.json", "Original bad_multiplier")
    analyze_json_file("bad_multiplier_extracted_cbc.json", "CBC extracted bad_multiplier")

    analyze_json_file("dot_product.json", "Original dot_product")
    analyze_json_file("dot_product_extracted_cbc.json", "CBC extracted dot_product")

    print("\nDemo completed!")