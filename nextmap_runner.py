#!/usr/bin/env python3

import sys
import os
import json
import tempfile
import argparse

# Add current directory to path for emap import
sys.path.insert(0, os.getcwd())

def run_nextmap(input_file, output_file, schema_path, max_iter=10, strategy="basic"):
    """Run nextmap optimization on input JSON file and write optimized result to output file."""
    try:
        import emap
        from emap.extracts.utils import db_to_normalized, normalized_to_json

        # Load input JSON
        with open(input_file, 'r') as f:
            data = json.load(f)

        # Extract the top module (assuming single module for now)
        if 'modules' not in data:
            raise ValueError('No modules found in input JSON')

        # Get the first module (could be made configurable)
        module_name = list(data['modules'].keys())[0]
        module_data = data['modules'][module_name]

        print(f"Processing module: {module_name}")

        # Create NetlistDB and build from JSON
        netlist = emap.NetlistDB(schema_path)
        netlist.build_from_json(module_data)
        netlist.rebuild()

        # Apply rewrite passes iteratively based on strategy
        total_rewrites = 0
        for iteration in range(max_iter):
            iteration_rewrites = 0

            try:
                if strategy == "retiming":
                    # Focus on DFF retiming optimizations
                    matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ['$adds', '$addu', '$muls', '$mulu'])
                    count = emap.rewrites.apply_dff_forward_aby_cell(netlist, matches)
                    iteration_rewrites += count

                elif strategy == "dsp":
                    # DSP technology mapping strategy like in eval_fir_v2.ipynb
                    # Apply wide multiplication splitting for large designs
                    try:
                        wide_mul_matches = emap.rewrites.ematch_wide_muls(netlist)
                        wide_mul_count = emap.rewrites.apply_wide_muls_split(netlist, wide_mul_matches)
                        if wide_mul_count > 0:
                            print(f"Applied {wide_mul_count} wide multiplication splits")
                            netlist.rebuild()

                        wide_dff_matches = emap.rewrites.ematch_wide_dff(netlist)
                        wide_dff_count = emap.rewrites.apply_wide_dff_split(netlist, wide_dff_matches)
                        if wide_dff_count > 0:
                            print(f"Applied {wide_dff_count} wide DFF splits")
                            netlist.rebuild()
                    except Exception as e:
                        print(f"Warning: Wide splitting failed: {e}")

                    # Standard rewrite rules for DSP optimization
                    comm_matches = emap.rewrites.ematch_comm(netlist, ['$adds', '$muls'])
                    iteration_rewrites += emap.rewrites.apply_comm(netlist, comm_matches)

                    dff_forward_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ['$adds', '$muls'])
                    iteration_rewrites += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_matches)

                    dff_backward_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ['$adds', '$muls'])
                    iteration_rewrites += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_matches)

                elif strategy == "comprehensive":
                    # Apply multiple rewrite rules like in the notebook
                    # Commutativity
                    comm_matches = emap.rewrites.ematch_comm(netlist, ['$adds', '$addu', '$muls', '$mulu'])
                    iteration_rewrites += emap.rewrites.apply_comm(netlist, comm_matches)

                    # Associativity
                    assoc_right_matches = emap.rewrites.ematch_assoc_to_right(netlist, ['$adds', '$addu', '$muls', '$mulu'])
                    iteration_rewrites += emap.rewrites.apply_assoc_to_right(netlist, assoc_right_matches)

                    assoc_left_matches = emap.rewrites.ematch_assoc_to_left(netlist, ['$adds', '$addu', '$muls', '$mulu'])
                    iteration_rewrites += emap.rewrites.apply_assoc_to_left(netlist, assoc_left_matches)

                    # DFF retiming
                    dff_forward_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ['$adds', '$addu', '$muls', '$mulu'])
                    iteration_rewrites += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_matches)

                    dff_backward_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ['$adds', '$addu', '$muls', '$mulu'])
                    iteration_rewrites += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_matches)

                else:  # basic strategy
                    # Simple DFF forward rewrite
                    matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ['$mulu'])
                    count = emap.rewrites.apply_dff_forward_aby_cell(netlist, matches)
                    iteration_rewrites += count

                if iteration_rewrites > 0:
                    netlist.rebuild()

            except Exception as e:
                print(f'Warning: Rewrite pass failed: {e}')

            total_rewrites += iteration_rewrites
            if iteration_rewrites == 0:
                break

        print(f'Applied {total_rewrites} total rewrites in {iteration + 1} iterations')

        # Apply DSP technology mapping if using DSP strategy
        if strategy == "dsp":
            try:
                # Define DSP rules similar to the notebook
                dsp_rules = {
                    "dsp_generic": {
                        "requirements": {
                            "dsp48e2": 1
                        },
                        "hidden_inputs": ["clk"],
                        "inputs": ["inputs"],
                        "outputs": ["outputs"]
                    }
                }

                print("Applying DSP technology mapping...")
                emap.rewrites.create_tech_tables(netlist, dsp_rules)
                emap.rewrites.techmap_dsp(netlist)

                # Use technology mapping extraction with DSP limits
                # Adjust DSP limit based on design size (rough heuristic)
                # Count cells from all cell tables
                aby_count = len(list(netlist.execute("SELECT * FROM aby_cells").fetchall()))
                ay_count = len(list(netlist.execute("SELECT * FROM ay_cells").fetchall()))
                absy_count = len(list(netlist.execute("SELECT * FROM absy_cells").fetchall()))
                total_cells = aby_count + ay_count + absy_count
                dsp_limit = max(16, total_cells)  # At least 16, more for larger designs

                print(f"Extracting with DSP limit: {dsp_limit}")

                def simple_cost_model(type_: str, *ports) -> float:
                    if type_ == "$dff":
                        return len(ports[0]) * 1.0
                    elif type_ in {"$muls", "$mulu"}:
                        return len(ports[0]) * len(ports[1]) * 1.0
                    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
                        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
                    elif type_.startswith("$"):
                        return len(ports[0]) * 1.0
                    return 0.0  # blackboxes or tech cells

                optimized_module = emap.extracts.ilp.extract_techmap_with_limit(
                    netlist, simple_cost_model, dsp_rules, {"dsp48e2": dsp_limit}, OutputFlag=False
                )

            except Exception as e:
                print(f"Warning: DSP technology mapping failed: {e}")
                # Fallback to normal extraction
                def cost_model(cell_type, *args):
                    return 1
                inputs, outputs, cells, dffs = db_to_normalized(netlist, cost_model)
                optimized_module = normalized_to_json(netlist, {}, inputs, outputs, cells, dffs)
        else:
            # Normal extraction for other strategies
            def cost_model(cell_type, *args):
                return 1  # Simple uniform cost

            inputs, outputs, cells, dffs = db_to_normalized(netlist, cost_model)
            optimized_module = normalized_to_json(netlist, {}, inputs, outputs, cells, dffs)

        # Create output JSON with same structure as input
        output_data = data.copy()
        output_data['modules'][module_name] = optimized_module
        output_data['creator'] = 'nextmap-yosys-plugin'

        # Write output JSON
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        return True

    except Exception as e:
        print(f'Error in nextmap processing: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Run nextmap optimization on Yosys JSON')
    parser.add_argument('input_file', help='Input JSON file')
    parser.add_argument('output_file', help='Output JSON file')
    parser.add_argument('--schema', default='./emap/schema.sql', help='Schema file path')
    parser.add_argument('--iterations', type=int, default=10, help='Maximum iterations')
    parser.add_argument('--strategy', choices=['basic', 'retiming', 'comprehensive', 'dsp'],
                       default='basic', help='Optimization strategy to use')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file {args.input_file} does not exist")
        sys.exit(1)

    if not os.path.exists(args.schema):
        print(f"Error: Schema file {args.schema} does not exist")
        sys.exit(1)

    success = run_nextmap(args.input_file, args.output_file, args.schema, args.iterations, args.strategy)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()