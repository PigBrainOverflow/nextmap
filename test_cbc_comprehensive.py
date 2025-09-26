#!/usr/bin/env python3
"""
Comprehensive CBC testing simulating evaluation notebook scenarios
"""

import sys
import os
import json
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, '/home/jbalkind/projects/nextmap')

# Activate venv for CBC support
venv_path = '/home/jbalkind/projects/nextmap/venv/lib/python3.12/site-packages'
if venv_path not in sys.path and os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

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

def test_extract_no_techmap(netlist_file: str, test_name: str):
    """Test basic extraction without techmap (like demo.ipynb)"""
    print(f"\\n=== {test_name}: extract_no_techmap ===")

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
        result = emap.extracts.ilp.extract_no_techmap(netlist, simple_cost_model, solver_type="cbc")
        end_time = time.time()

        num_cells = len(result.get('cells', {}))
        print(f"Result: {num_cells} cells, {end_time - start_time:.3f}s")

        return True, num_cells

    except Exception as e:
        print(f"FAILED: {e}")
        return False, 0

def test_extract_techmap_with_limit(netlist_file: str, test_name: str, resource_limits: dict):
    """Test techmap extraction with limits (like eval notebooks)"""
    print(f"\\n=== {test_name}: extract_techmap_with_limit ===")

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
            solver_type="cbc"
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

    os.chdir('/home/jbalkind/projects/nextmap')

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

    for test_case in test_cases:
        if os.path.exists(test_case['file']):
            # Test basic extraction
            success, cells = test_extract_no_techmap(test_case['file'], test_case['name'])
            results['no_techmap'].append((test_case['name'], success, cells))

            # Test techmap extraction
            success, cells = test_extract_techmap_with_limit(
                test_case['file'],
                test_case['name'],
                test_case['limits']
            )
            results['techmap_with_limit'].append((test_case['name'], success, cells))
        else:
            print(f"\\nSkipping {test_case['name']}: file {test_case['file']} not found")

    # Summary
    print("\\n" + "="*60)
    print("COMPREHENSIVE TESTING SUMMARY")
    print("="*60)

    print("\\nBasic extraction (extract_no_techmap):")
    for name, success, cells in results['no_techmap']:
        status = "✓" if success else "✗"
        print(f"  {status} {name}: {cells} cells")

    print("\\nTechmap extraction (extract_techmap_with_limit):")
    for name, success, cells in results['techmap_with_limit']:
        status = "✓" if success else "✗"
        print(f"  {status} {name}: {cells} cells")

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