#!/usr/bin/env python3
"""
Test script for the solver migration from Gurobi to CBC.
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

try:
    from emap.extracts.solver_interface import create_solver, GRB, quicksum

    print("Testing solver interface...")

    # Test with auto selection (should try Gurobi first, fallback to CBC)
    print("\n=== Testing auto solver selection ===")
    try:
        solver = create_solver("auto")
        print(f"Auto solver selected: {type(solver).__name__}")

        # Simple test problem
        x = solver.addVars(2, vtype=GRB.BINARY, name="x")
        y = solver.addVar(vtype=GRB.BINARY, name="y")

        # Constraint: x[0] + x[1] >= y
        # Objective: minimize x[0] + x[1] + y
        solver.addConstr(x[0] + x[1] >= y)
        solver.addConstr(y >= 1)  # Force y to be 1

        obj = quicksum([x[0], x[1], y], solver=solver)
        solver.setObjective(obj, GRB.MINIMIZE)

        print("Solving...")
        solver.optimize()

        print(f"Status: {solver.status}")
        print(f"Objective value: {solver.objVal}")

        # Check solution
        for var in solver.getVars():
            print(f"{var.name} = {var.X}")

    except Exception as e:
        print(f"Auto solver test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test CBC specifically
    print("\n=== Testing CBC solver specifically ===")
    try:
        solver_cbc = create_solver("cbc")
        print(f"CBC solver created: {type(solver_cbc).__name__}")

        # Simple test
        x = solver_cbc.addVar(vtype=GRB.BINARY, name="x1")
        y = solver_cbc.addVar(vtype=GRB.BINARY, name="x2")

        solver_cbc.addConstr(x + y >= 1)
        solver_cbc.setObjective(x + y, GRB.MINIMIZE)

        print("Solving with CBC...")
        solver_cbc.optimize()

        print(f"Status: {solver_cbc.status}")
        print(f"Objective value: {solver_cbc.objVal}")

    except Exception as e:
        print(f"CBC solver test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test Gurobi if available
    print("\n=== Testing Gurobi solver specifically ===")
    try:
        solver_grb = create_solver("gurobi")
        print(f"Gurobi solver created: {type(solver_grb).__name__}")

    except Exception as e:
        print(f"Gurobi solver not available: {e}")

    print("\nSolver interface test completed.")

except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()