#!/usr/bin/env python3
"""
Test script to verify solver selection behavior in the emap interface.
This will help diagnose why changing solver_type doesn't seem to change the actual solver.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import emap
import json

def test_solver_selection():
    """Test that different solver_type values actually use different solvers"""

    print("=== Solver Selection Test ===")

    # Test 1: Check what solvers are available
    print("\n1. Testing solver availability:")

    try:
        from emap.extracts.solver_interface import GurobiInterface
        print("✓ Gurobi interface available")
        gurobi_available = True
    except Exception as e:
        print(f"✗ Gurobi interface not available: {e}")
        gurobi_available = False

    try:
        from emap.extracts.solver_interface import CBCInterface
        print("✓ CBC interface available")
        cbc_available = True
    except Exception as e:
        print(f"✗ CBC interface not available: {e}")
        cbc_available = False

    # Test 2: Check what create_solver returns for different parameters
    print("\n2. Testing solver creation:")

    from emap.extracts.solver_interface import create_solver

    test_cases = ["auto", "gurobi", "cbc"]

    for solver_type in test_cases:
        print(f"\n   Testing solver_type='{solver_type}':")
        try:
            solver = create_solver(solver_type=solver_type)
            solver_class = solver.__class__.__name__
            print(f"   ✓ Created: {solver_class}")

            # Check if the solver has a method to identify itself
            if hasattr(solver, 'solver_name'):
                print(f"   ✓ Solver name: {solver.solver_name}")
            elif 'Gurobi' in solver_class:
                print("   ✓ Identified as: Gurobi")
            elif 'CBC' in solver_class:
                print("   ✓ Identified as: CBC")

        except Exception as e:
            print(f"   ✗ Failed: {e}")

    # Test 3: Create a minimal ILP problem and solve with different solvers
    print("\n3. Testing actual solver execution:")

    # Create a simple test netlist
    SCHEMA_PATH = "emap/schema.sql"
    netlist = emap.NetlistDB(SCHEMA_PATH)

    # Add a minimal test circuit (just a few cells for testing)
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

    def simple_cost_model(type_: str, *ports) -> float:
        return 1.0

    # Test extraction with different solver types
    for solver_type in ["auto", "gurobi", "cbc"]:
        print(f"\n   Testing extraction with solver_type='{solver_type}':")
        try:
            # Use a very verbose approach to capture any output
            result = emap.extracts.ilp.extract_no_techmap(
                netlist,
                simple_cost_model,
                solver_type=solver_type,
                OutputFlag=True  # Enable verbose output to see which solver is used
            )
            print(f"   ✓ Extraction completed successfully")

        except Exception as e:
            print(f"   ✗ Extraction failed: {e}")

if __name__ == "__main__":
    test_solver_selection()