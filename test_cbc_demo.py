#!/usr/bin/env python3
"""
Test CBC migration using demo examples from demo.ipynb
"""

import sys
import os
import json

# Add the project root to the path so we can import modules
sys.path.insert(0, '/home/jbalkind/projects/nextmap')

# Activate venv for CBC support
venv_path = '/home/jbalkind/projects/nextmap/venv/lib/python3.12/site-packages'
if venv_path not in sys.path and os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

import emap

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

def test_retiming_example():
    """Test the retiming example from demo.ipynb using CBC."""
    print("=== Testing Retiming Example with CBC ===")

    # Check if we have the test file
    if not os.path.exists("tests/bad_multiplier.v"):
        print("Skipping retiming test - test file not found")
        return

    # Generate JSON if needed
    if not os.path.exists("bad_multiplier.json"):
        print("Generating JSON file with Yosys...")
        os.system("yosys -q -p 'read_verilog tests/bad_multiplier.v; proc; opt_merge; opt_clean; write_json bad_multiplier.json'")

    if not os.path.exists("bad_multiplier.json"):
        print("Could not generate JSON file - skipping test")
        return

    try:
        TEST_NAME = "bad_multiplier"
        SCHEMA_PATH = "emap/schema.sql"
        netlist = emap.NetlistDB(SCHEMA_PATH)
        with open(f"{TEST_NAME}.json", "r") as f:
            netlist.build_from_json(json.load(f)["modules"]["top"])

        netlist.rebuild()
        print("Netlist loaded successfully")

        # Apply retiming rewrites
        cnt = 1
        total_rewrites = 0
        while cnt > 0:
            dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$addu", "$muls", "$mulu"])

            cnt = emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
            if cnt > 0:
                print(f"Applied {cnt} rewrites")
                total_rewrites += cnt
            netlist.rebuild()

        print(f"Total rewrites applied: {total_rewrites}")

        # Extract using CBC
        print("Extracting with CBC solver...")
        mod = emap.extracts.ilp.extract_no_techmap(netlist, simple_cost_model, solver_type="cbc")
        print("Extraction completed successfully!")

        # Save result
        with open(f"{TEST_NAME}_extracted_cbc.json", "w") as f:
            json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)

        print(f"Results saved to {TEST_NAME}_extracted_cbc.json")

        # Count DFFs in original vs extracted
        original_dffs = count_dffs_in_json(f"{TEST_NAME}.json")
        extracted_dffs = count_dffs_in_json(f"{TEST_NAME}_extracted_cbc.json")

        print(f"Original DFFs: {original_dffs}")
        print(f"Extracted DFFs: {extracted_dffs}")
        print(f"DFFs saved: {original_dffs - extracted_dffs}")

    except Exception as e:
        print(f"Error in retiming test: {e}")
        import traceback
        traceback.print_exc()

def test_techmap_example():
    """Test the technology mapping example from demo.ipynb using CBC."""
    print("\n=== Testing Technology Mapping Example with CBC ===")

    # Check if we have the test file
    if not os.path.exists("tests/dot_product.v"):
        print("Skipping techmap test - test file not found")
        return

    # Generate JSON if needed
    if not os.path.exists("dot_product.json"):
        print("Generating JSON file with Yosys...")
        os.system("yosys -q -p 'read_verilog tests/dot_product.v; proc; opt_merge; opt_clean; write_json dot_product.json'")

    if not os.path.exists("dot_product.json"):
        print("Could not generate JSON file - skipping test")
        return

    # Define DSP rules from demo
    dsp_rules = {
        "signed_mul_1_stage_26_17_48_bit": {
            "requirements": {
                "dsp48e2": 1
            },
            "hidden_inputs": ["clk"],
            "inputs": ["a", "b"],
            "outputs": ["p"],
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

    try:
        TEST_NAME = "dot_product"
        SCHEMA_PATH = "emap/schema.sql"
        netlist = emap.NetlistDB(SCHEMA_PATH)
        with open(f"{TEST_NAME}.json", "r") as f:
            netlist.build_from_json(json.load(f)["modules"]["top"])

        netlist.rebuild()
        print("Netlist loaded successfully")

        # Apply various rewrites
        cnt = 1
        total_rewrites = 0
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
                total_rewrites += cnt
            netlist.rebuild()

        print(f"Total rewrites applied: {total_rewrites}")

        # Technology mapping
        print("Applying technology mapping...")
        emap.rewrites.create_tech_tables(netlist, dsp_rules)
        emap.rewrites.rewrite_tech(netlist, dsp_rules)

        # Extract using CBC
        print("Extracting with CBC solver...")

        def techmap_cost_model(type_: str, *ports) -> float:
            if type_ == "$dff":
                return len(ports[0]) * 1.0
            elif type_ in {"$muls", "$mulu"}:
                return len(ports[0]) * len(ports[1]) * 1.0
            elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
                return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
            elif type_.startswith("$"):  # other types
                return len(ports[0]) * 1.0
            return 0.0  # blackboxes or tech cells

        mod = emap.extracts.ilp.extract_techmap_with_limit(
            netlist, techmap_cost_model, dsp_rules, {"dsp48e2": 2}, solver_type="cbc")
        print("Technology mapping extraction completed successfully!")

        # Save result
        with open(f"{TEST_NAME}_extracted_cbc.json", "w") as f:
            json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)

        print(f"Results saved to {TEST_NAME}_extracted_cbc.json")

        # Analyze results
        print("Technology mapping results:")
        print(f"- Used DSP limits: dsp48e2 <= 2")
        print(f"- Generated {TEST_NAME}_extracted_cbc.json")

    except Exception as e:
        print(f"Error in technology mapping test: {e}")
        import traceback
        traceback.print_exc()

def count_dffs_in_json(filename):
    """Count DFF cells in a JSON netlist."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        cells = data.get("modules", {}).get("top", {}).get("cells", {})
        dff_count = 0
        for cell in cells.values():
            if cell.get("type", "").startswith("$dff"):
                dff_count += 1
        return dff_count
    except:
        return 0

if __name__ == "__main__":
    print("Testing CBC migration with demo examples...")

    # Change to project directory
    os.chdir('/home/jbalkind/projects/nextmap')

    test_retiming_example()
    test_techmap_example()

    print("\nCBC migration testing completed!")