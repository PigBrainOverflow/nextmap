#!/usr/bin/env python3
"""
Test both CBC and Gurobi solvers on all evaluation notebooks
"""

import sys
import os
import json
import time
from pathlib import Path

# Add the current directory to the path (assuming we're in nextmap root)
sys.path.insert(0, os.path.abspath('.'))

import emap

def standard_cost_model(type_: str, *ports) -> float:
    """Standard cost model used in evaluations"""
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    else:
        return len(ports[0]) * 1.0

def run_extraction(netlist_file: str, description: str = "", solver_type: str = "cbc"):
    """Run extraction on a netlist file with specified solver"""
    print(f"\n=== Testing {netlist_file} {description} (solver: {solver_type}) ===")

    try:
        # Load netlist
        if not os.path.exists(netlist_file):
            print(f"File not found: {netlist_file}")
            return None

        with open(netlist_file, 'r') as f:
            netlist_data = json.load(f)

        # Create and build netlist
        netlist = emap.NetlistDB('emap/schema.sql')
        netlist.build_from_json(netlist_data['modules']['top'])
        netlist.rebuild()

        print(f"Loaded netlist with {len(netlist_data['modules']['top'].get('cells', {}))} original cells")

        # Apply rewrites
        total_rewrites = 0
        cnt = 1
        while cnt > 0:
            matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ['$adds', '$addu', '$muls', '$mulu'])
            cnt = emap.rewrites.apply_dff_forward_aby_cell(netlist, matches)
            total_rewrites += cnt
            netlist.rebuild()

        print(f"Applied {total_rewrites} rewrites")

        # Run CBC extraction
        start_time = time.time()
        result = emap.extracts.ilp.extract_no_techmap(netlist, standard_cost_model, solver_type=solver_type)
        end_time = time.time()

        num_cells = len(result.get('cells', {}))
        print(f"{solver_type.upper()} result: {num_cells} cells in {end_time - start_time:.2f}s")

        if num_cells > 0:
            cell_types = {}
            for cell_name, cell_data in result.get('cells', {}).items():
                cell_type = cell_data.get('type', 'unknown')
                cell_types[cell_type] = cell_types.get(cell_type, 0) + 1
            print(f"Cell types: {dict(cell_types)}")

        return {
            'file': netlist_file,
            'cells': num_cells,
            'time': end_time - start_time,
            'cell_types': cell_types if num_cells > 0 else {},
            'success': True
        }

    except Exception as e:
        print(f"Error processing {netlist_file}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'file': netlist_file,
            'error': str(e),
            'success': False
        }

def main():
    """Test both solvers on various evaluation files"""
    print("Testing solvers on evaluation notebooks...")

    # Assume we're already in the nextmap root directory
    # os.chdir not needed

    # Test files based on common evaluation patterns
    test_files = []

    # Look for JSON files that might be test cases
    json_files = list(Path('.').glob('*.json'))

    # Common test cases
    common_tests = [
        'bad_multiplier.json',
        'dot_product.json',
        'systolic.json',
        'fir.json',
        'fft.json',
        'nerv.json',
        'mem.json',
        'handcrafted.json'
    ]

    # Add files that exist
    for test_file in common_tests:
        if os.path.exists(test_file):
            test_files.append(test_file)

    # Also check for any other JSON files that look like test cases
    for json_file in json_files:
        json_file_str = str(json_file)
        if json_file_str not in test_files and not json_file_str.endswith('_extracted_cbc.json'):
            # Skip files that are clearly outputs or configs
            if not any(skip in json_file_str for skip in ['config', 'output', 'result', 'extracted']):
                test_files.append(json_file_str)

    print(f"Found {len(test_files)} test files: {test_files}")

    results = []

    # Test with both solvers
    solvers_to_test = ["cbc", "gurobi"]

    for solver_type in solvers_to_test:
        print(f"\n{'='*60}")
        print(f"TESTING WITH {solver_type.upper()} SOLVER")
        print(f"{'='*60}")

        for test_file in test_files:
            result = run_extraction(test_file, f"({test_file})", solver_type=solver_type)
            if result:
                result['solver'] = solver_type
                results.append(result)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Total tests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    # Summary by solver
    for solver in ['cbc', 'gurobi']:
        solver_results = [r for r in results if r.get('solver') == solver]
        solver_successful = [r for r in solver_results if r['success']]
        print(f"\n{solver.upper()} solver: {len(solver_successful)}/{len(solver_results)} successful")

    if successful:
        print("\nSuccessful extractions:")
        for result in successful:
            solver_info = f" [{result.get('solver', 'unknown')}]" if 'solver' in result else ""
            print(f"  {result['file']}{solver_info}: {result['cells']} cells ({result['time']:.2f}s)")

    if failed:
        print("\nFailed extractions:")
        for result in failed:
            solver_info = f" [{result.get('solver', 'unknown')}]" if 'solver' in result else ""
            print(f"  {result['file']}{solver_info}: {result['error']}")

    # Check for any zero-cell results (potential issues)
    zero_cell_results = [r for r in successful if r['cells'] == 0]
    if zero_cell_results:
        print(f"\nWarning: {len(zero_cell_results)} tests produced 0 cells:")
        for result in zero_cell_results:
            solver_info = f" [{result.get('solver', 'unknown')}]" if 'solver' in result else ""
            print(f"  {result['file']}{solver_info}")

    # Compare results between solvers for same files
    print("\nSolver comparison:")
    files_tested = set(r['file'] for r in successful)
    for file in files_tested:
        file_results = [r for r in successful if r['file'] == file]
        if len(file_results) > 1:
            results_by_solver = {r['solver']: r for r in file_results}
            if 'cbc' in results_by_solver and 'gurobi' in results_by_solver:
                cbc_cells = results_by_solver['cbc']['cells']
                gurobi_cells = results_by_solver['gurobi']['cells']
                cbc_time = results_by_solver['cbc']['time']
                gurobi_time = results_by_solver['gurobi']['time']
                print(f"  {file}: CBC={cbc_cells} cells ({cbc_time:.2f}s), Gurobi={gurobi_cells} cells ({gurobi_time:.2f}s)")

if __name__ == "__main__":
    main()