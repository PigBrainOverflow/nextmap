#!/usr/bin/env python3
"""
Comprehensive CBC testing simulating evaluation notebook scenarios
"""

import sys
import os
import json
import time
from pathlib import Path

# Add the current directory to the path (assuming we're in nextmap root)
sys.path.insert(0, os.path.abspath('.'))

import emap

def simple_cost_model(type_: str, *ports) -> float:
    """Standard cost model used in evaluations"""
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0

def test_extract_no_techmap(netlist_file: str, test_name: str, solver_type: str = "cbc"):
    """Test basic extraction without techmap (like demo.ipynb)"""
    print(f"\\n=== {test_name}: extract_no_techmap ({solver_type}) ===")

    try:
        with open(netlist_file, 'r') as f:
            netlist_data = json.load(f)

        netlist = emap.NetlistDB('emap/schema.sql')
        netlist.build_from_json(netlist_data['modules']['top'])
        netlist.rebuild()

        # Apply standard rewrites
        cnt = 1
        total_rewrites = 0
        while cnt > 0:
            matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ['$adds', '$addu', '$muls', '$mulu'])
            cnt = emap.rewrites.apply_dff_forward_aby_cell(netlist, matches)
            total_rewrites += cnt
            netlist.rebuild()

        # Run extraction with CBC
        start_time = time.time()
        result = emap.extracts.ilp.extract_no_techmap(netlist, simple_cost_model, solver_type=solver_type)
        end_time = time.time()

        num_cells = len(result.get('cells', {}))
        print(f"Result: {num_cells} cells, {end_time - start_time:.3f}s")

        return True, num_cells

    except Exception as e:
        print(f"FAILED: {e}")
        return False, 0

def test_extract_techmap_with_limit(netlist_file: str, test_name: str, resource_limits: dict, solver_type: str = "cbc"):
    """Test techmap extraction with limits (like eval notebooks)"""
    print(f"\\n=== {test_name}: extract_techmap_with_limit ({solver_type}) ===")

    # Simplified DSP rules for testing
    dsp_rules = {
        "simple_mul_dff": {
            "requirements": {"dsp48e2": 1},
            "hidden_inputs": ["clk"],
            "inputs": ["a", "b"],
            "outputs": ["p"],
            "match_sql": '''
                SELECT mul1.a, mul1.b, dff1.q
                FROM dffs AS dff1 JOIN aby_cells AS mul1
                ON dff1.d = mul1.y
                WHERE mul1.type = '$muls'
                    AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18
            '''
        }
    }

    try:
        with open(netlist_file, 'r') as f:
            netlist_data = json.load(f)

        netlist = emap.NetlistDB('emap/schema.sql')
        netlist.build_from_json(netlist_data['modules']['top'])
        netlist.rebuild()

        # Apply comprehensive rewrites (like eval notebooks)
        cnt = 1
        total_rewrites = 0
        while cnt > 0:
            comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
            dff_forward_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
            dff_backward_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])

            cnt = emap.rewrites.apply_comm(netlist, comm_matches)
            cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_matches)
            cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_matches)
            total_rewrites += cnt
            netlist.rebuild()

        # Apply tech mapping
        emap.rewrites.create_tech_tables(netlist, dsp_rules)
        emap.rewrites.rewrite_tech(netlist, dsp_rules)

        # Run extraction with CBC and resource limits
        start_time = time.time()
        result = emap.extracts.ilp.extract_techmap_with_limit(
            netlist,
            simple_cost_model,
            dsp_rules,
            resource_limits,
            solver_type=solver_type
        )
        end_time = time.time()

        num_cells = len(result.get('cells', {}))
        print(f"Result: {num_cells} cells, {end_time - start_time:.3f}s")

        return True, num_cells

    except Exception as e:
        print(f"FAILED: {e}")
        return False, 0

def main():
    """Run comprehensive CBC testing"""
    print("=== COMPREHENSIVE CBC TESTING ===")
    print("Simulating evaluation notebook scenarios with CBC solver")

    # Assume we're already in the nextmap root directory
    # os.chdir not needed

    test_cases = [
        {
            'file': 'bad_multiplier.json',
            'name': 'Bad Multiplier',
            'limits': {'dsp48e2': 4}
        },
        {
            'file': 'dot_product.json',
            'name': 'Dot Product',
            'limits': {'dsp48e2': 8}
        },
        {
            'file': 'eval/out/fir_n16_w8.json',
            'name': 'FIR n16_w8',
            'limits': {'dsp48e2': 16}
        }
    ]

    results = {
        'no_techmap': [],
        'techmap_with_limit': []
    }

    # Test with both solvers
    solvers_to_test = ["cbc", "gurobi"]

    for solver_type in solvers_to_test:
        print(f"\\n{'='*60}")
        print(f"TESTING WITH {solver_type.upper()} SOLVER")
        print(f"{'='*60}")

        for test_case in test_cases:
            if os.path.exists(test_case['file']):
                # Test basic extraction
                success, cells = test_extract_no_techmap(test_case['file'], test_case['name'], solver_type)
                results['no_techmap'].append((test_case['name'], success, cells, solver_type))

                # Test techmap extraction
                success, cells = test_extract_techmap_with_limit(
                    test_case['file'],
                    test_case['name'],
                    test_case['limits'],
                    solver_type
                )
                results['techmap_with_limit'].append((test_case['name'], success, cells, solver_type))
            else:
                print(f"\\nSkipping {test_case['name']}: file {test_case['file']} not found")

    # Summary
    print("\\n" + "="*60)
    print("COMPREHENSIVE TESTING SUMMARY")
    print("="*60)

    print("\\nBasic extraction (extract_no_techmap):")
    for name, success, cells, solver_type in results['no_techmap']:
        status = "✓" if success else "✗"
        print(f"  {status} {name} [{solver_type}]: {cells} cells")

    print("\\nTechmap extraction (extract_techmap_with_limit):")
    for name, success, cells, solver_type in results['techmap_with_limit']:
        status = "✓" if success else "✗"
        print(f"  {status} {name} [{solver_type}]: {cells} cells")

    # Compare solver performance
    print("\\nSolver comparison:")
    test_names = list(set(name for name, _, _, _ in results['no_techmap']))
    for test_name in test_names:
        # Basic extraction comparison
        basic_results = {solver: (success, cells) for name, success, cells, solver in results['no_techmap'] if name == test_name}
        if len(basic_results) == 2:
            cbc_success, cbc_cells = basic_results.get('cbc', (False, 0))
            gurobi_success, gurobi_cells = basic_results.get('gurobi', (False, 0))
            print(f"  {test_name} (basic): CBC={cbc_cells} cells, Gurobi={gurobi_cells} cells")

        # Techmap extraction comparison
        techmap_results = {solver: (success, cells) for name, success, cells, solver in results['techmap_with_limit'] if name == test_name}
        if len(techmap_results) == 2:
            cbc_success, cbc_cells = techmap_results.get('cbc', (False, 0))
            gurobi_success, gurobi_cells = techmap_results.get('gurobi', (False, 0))
            print(f"  {test_name} (techmap): CBC={cbc_cells} cells, Gurobi={gurobi_cells} cells")

    # Overall success rate
    total_tests = len(results['no_techmap']) + len(results['techmap_with_limit'])
    successful_tests = sum(1 for _, success, _ in results['no_techmap'] + results['techmap_with_limit'] if success)

    print(f"\\nOverall: {successful_tests}/{total_tests} tests passed ({100*successful_tests/total_tests:.0f}%)")

    if successful_tests == total_tests:
        print("\\n🎉 ALL TESTS PASSED! CBC solver is working correctly for all evaluation scenarios.")
    else:
        print(f"\\n⚠️  {total_tests - successful_tests} test(s) failed. Check the detailed output above.")

if __name__ == "__main__":
    main()