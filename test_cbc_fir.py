#!/usr/bin/env python3
"""
Test CBC migration using FIR filter example from eval_fir.ipynb
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
    "signed_muladd_1_stage_26_17_48_bit": {
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
                AND width_of(mul1.a) <= 26 AND width_of(mul1.b) <= 17 AND width_of(add1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    }
}

def test_fir_with_cbc():
    """Test FIR filter design with CBC solver."""
    print("=== Testing FIR Filter with CBC ===")

    # Check if we have the test file
    if not os.path.exists("eval/fir/fir_n16_w8.v"):
        print("Skipping FIR test - test file not found")
        return

    # Ensure output directory exists
    os.makedirs("eval/out", exist_ok=True)

    # Generate JSON if needed
    if not os.path.exists("eval/out/fir_n16_w8.json"):
        print("Generating JSON file with Yosys...")
        os.system("yosys -q -p 'read_verilog eval/fir/fir_n16_w8.v; proc; opt_merge; opt_clean; write_json eval/out/fir_n16_w8.json'")

    if not os.path.exists("eval/out/fir_n16_w8.json"):
        print("Could not generate JSON file - skipping test")
        return

    try:
        TEST_NAME = "fir_n16_w8"
        SCHEMA_PATH = "emap/schema.sql"
        netlist = emap.NetlistDB(SCHEMA_PATH)

        print("Loading FIR netlist...")
        with open(f"eval/out/{TEST_NAME}.json", "r") as f:
            netlist.build_from_json(json.load(f)["modules"]["top"])

        netlist.rebuild()
        print("Netlist loaded successfully")

        # Apply rewrites (similar to eval_fir.ipynb)
        print("Applying equality saturation rewrites...")
        cnt = 1
        total_rewrites = 0
        while cnt > 0:
            comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
            dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
            dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])

            cnt = emap.rewrites.apply_comm(netlist, comm_matches)
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

        # Extract using CBC with DSP limit
        print("Extracting with CBC solver (DSP limit: 16)...")
        mod = emap.extracts.ilp.extract_techmap_with_limit(
            netlist, simple_cost_model, dsp_rules, {"dsp48e2": 16}, solver_type="cbc")
        print("Technology mapping extraction completed successfully!")

        # Save result
        output_file = f"eval/out/{TEST_NAME}_extracted_cbc.json"
        with open(output_file, "w") as f:
            json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)

        print(f"Results saved to {output_file}")

        # Analyze results
        print("\nAnalyzing results...")
        analyze_design(output_file)

    except Exception as e:
        print(f"Error in FIR test: {e}")
        import traceback
        traceback.print_exc()

def analyze_design(json_file):
    """Analyze the extracted design."""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        cells = data.get("modules", {}).get("top", {}).get("cells", {})

        # Count cell types
        cell_counts = {}
        dsp_cells = []

        for name, cell in cells.items():
            cell_type = cell.get("type", "unknown")
            cell_counts[cell_type] = cell_counts.get(cell_type, 0) + 1

            # Look for DSP-related cells
            if "signed_mul" in cell_type or "dsp" in cell_type.lower():
                dsp_cells.append((name, cell_type))

        print(f"Total cells: {len(cells)}")
        print("Cell type breakdown:")
        for cell_type, count in sorted(cell_counts.items()):
            print(f"  {cell_type}: {count}")

        if dsp_cells:
            print(f"\nDSP cells found ({len(dsp_cells)}):")
            for name, cell_type in dsp_cells:
                print(f"  {name}: {cell_type}")
        else:
            print("\nNo DSP cells found in extracted design")

        # Count resource usage
        dsp_usage = sum(1 for _, cell_type in dsp_cells if "signed_mul" in cell_type)
        print(f"\nDSP48E2 usage: {dsp_usage}/16")

    except Exception as e:
        print(f"Error analyzing design: {e}")

if __name__ == "__main__":
    print("Testing CBC migration with FIR filter example...")

    # Change to project directory
    os.chdir('/home/jbalkind/projects/nextmap')

    test_fir_with_cbc()

    print("\nCBC FIR filter testing completed!")