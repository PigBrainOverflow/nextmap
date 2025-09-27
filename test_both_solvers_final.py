#!/usr/bin/env python3
"""
Quick test to verify both solvers work with the updated test files
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import emap
import json

def test_solver_selection():
    """Test that both solvers work correctly"""
    print("=== Testing Both Solvers ===")

    # Create a minimal test netlist
    SCHEMA_PATH = "emap/schema.sql"
    netlist = emap.NetlistDB(SCHEMA_PATH)

    test_module = {
        "cells": {
            "test_add": {
                "type": "$add",
                "parameters": {"A_SIGNED": False, "A_WIDTH": 4, "B_SIGNED": False, "B_WIDTH": 4, "Y_WIDTH": 5},
                "port_directions": {"A": "input", "B": "input", "Y": "output"},
                "connections": {"A": [1, 2, 3, 4], "B": [5, 6, 7, 8], "Y": [9, 10, 11, 12, 13]}
            }
        },
        "ports": {},
        "netnames": {}
    }

    netlist.build_from_json(test_module)  # Simple module without DFFs
    netlist.rebuild()

    def simple_cost_model(type_: str, *ports) -> float:
        if type_ == "$dff":
            return len(ports[0]) * 1.0
        elif type_ in {"$muls", "$mulu"}:
            return len(ports[0]) * len(ports[1]) * 1.0
        elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
            return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
        return len(ports[0]) * 1.0

    results = {}

    # Test all three modes
    for solver_type in ['auto', 'gurobi', 'cbc']:
        print(f"\n--- Testing solver_type='{solver_type}' ---")

        try:
            start_time = emap.time.time() if hasattr(emap, 'time') else __import__('time').time()

            result = emap.extracts.ilp.extract_no_techmap(
                netlist,
                simple_cost_model,
                solver_type=solver_type,
                OutputFlag=False  # Suppress verbose output
            )

            end_time = emap.time.time() if hasattr(emap, 'time') else __import__('time').time()

            num_cells = len(result.get('cells', {}))
            print(f"✓ Success: {num_cells} cells extracted in {end_time - start_time:.3f}s")

            results[solver_type] = {
                'success': True,
                'cells': num_cells,
                'time': end_time - start_time
            }

        except Exception as e:
            print(f"✗ Failed: {e}")
            results[solver_type] = {
                'success': False,
                'error': str(e)
            }

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")

    for solver_type, result in results.items():
        if result['success']:
            print(f"✓ {solver_type:>6}: {result['cells']} cells ({result['time']:.3f}s)")
        else:
            print(f"✗ {solver_type:>6}: {result['error']}")

    # Verify consistency
    successful_results = [r for r in results.values() if r['success']]
    if len(successful_results) > 1:
        cell_counts = [r['cells'] for r in successful_results]
        if len(set(cell_counts)) == 1:
            print(f"\n✓ All solvers produced consistent results ({cell_counts[0]} cells)")
        else:
            print(f"\n⚠ Warning: Solvers produced different cell counts: {cell_counts}")

    return results

if __name__ == "__main__":
    print("Testing dual solver support in Nextmap")
    test_solver_selection()
    print("\nTest completed!")