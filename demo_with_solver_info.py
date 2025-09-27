#!/usr/bin/env python3
"""
Demo script that shows solver selection clearly.
This demonstrates the behavior and adds logging to show which solver is used.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import emap
import json

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

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

netlist.build_from_json(test_module)
netlist.rebuild()

def test_solver_with_logging(solver_type):
    print(f"\n=== Testing solver_type='{solver_type}' ===")

    # Temporarily patch create_solver to add logging
    from emap.extracts.solver_interface import create_solver
    original_create_solver = create_solver

    def logged_create_solver(solver_type_inner="auto", **kwargs):
        print(f"  → create_solver called with solver_type='{solver_type_inner}'")

        if solver_type_inner == "auto":
            print("  → Auto mode: trying Gurobi first...")
            try:
                from emap.extracts.solver_interface import GurobiInterface
                solver = GurobiInterface(**kwargs)
                print("  ✓ Successfully created GurobiInterface")
                return solver
            except Exception as e:
                print(f"  ✗ Gurobi failed: {e}")
                print("  → Auto mode: falling back to CBC...")
                try:
                    from emap.extracts.solver_interface import CBCInterface
                    solver = CBCInterface(**kwargs)
                    print("  ✓ Successfully created CBCInterface")
                    return solver
                except Exception as e2:
                    print(f"  ✗ CBC also failed: {e2}")
                    raise e2
        elif solver_type_inner == "gurobi":
            print("  → Explicitly requesting Gurobi...")
            from emap.extracts.solver_interface import GurobiInterface
            solver = GurobiInterface(**kwargs)
            print("  ✓ Successfully created GurobiInterface")
            return solver
        elif solver_type_inner == "cbc":
            print("  → Explicitly requesting CBC...")
            from emap.extracts.solver_interface import CBCInterface
            solver = CBCInterface(**kwargs)
            print("  ✓ Successfully created CBCInterface")
            return solver
        else:
            raise ValueError(f"Unknown solver type: {solver_type_inner}")

    # Monkey patch for this test
    import emap.extracts.ilp
    emap.extracts.ilp.create_solver = logged_create_solver

    try:
        result = emap.extracts.ilp.extract_no_techmap(
            netlist,
            simple_cost_model,
            solver_type=solver_type,
            OutputFlag=False  # Reduce Gurobi output for clarity
        )
        print(f"  ✓ Extraction completed successfully")
        return result
    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")
        return None
    finally:
        # Restore original function
        emap.extracts.ilp.create_solver = original_create_solver

if __name__ == "__main__":
    print("Testing solver selection behavior with detailed logging\n")

    test_cases = ["auto", "gurobi", "cbc"]

    for solver_type in test_cases:
        test_solver_with_logging(solver_type)

    print("\n" + "="*60)
    print("CONCLUSION:")
    print("- solver_type='auto' ALWAYS chooses Gurobi when available")
    print("- solver_type='gurobi' explicitly uses Gurobi")
    print("- solver_type='cbc' explicitly uses CBC")
    print("- To force CBC usage, you must use solver_type='cbc'")
    print("="*60)