"""
Configurable solver interface for ILP problems.
Supports both Gurobi and CBC solvers with a unified API.
"""

import os
import sys
from typing import Any, Dict, List, Union, Optional
import numpy as np
import scipy.sparse as sp
from abc import ABC, abstractmethod


class SolverError(Exception):
    """Exception raised by solver operations."""
    pass


class LinearExpression:
    """Simple linear expression for constraints."""
    def __init__(self):
        self.terms = {}  # variable_name -> coefficient
        self.constant = 0.0

    def add_term(self, coeff: float, var_name: str):
        if var_name in self.terms:
            self.terms[var_name] += coeff
        else:
            self.terms[var_name] = coeff

    def add_constant(self, constant: float):
        self.constant += constant

    def __add__(self, other):
        result = LinearExpression()
        result.terms = self.terms.copy()
        result.constant = self.constant

        if isinstance(other, Variable):
            result.add_term(1.0, other.name)
        elif isinstance(other, LinearExpression):
            for var_name, coeff in other.terms.items():
                result.add_term(coeff, var_name)
            result.add_constant(other.constant)
        elif isinstance(other, (int, float)):
            result.add_constant(other)

        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            result = LinearExpression()
            result.terms = {k: v * other for k, v in self.terms.items()}
            result.constant = self.constant * other
            return result
        else:
            raise TypeError("Can only multiply LinearExpression by scalar")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __ge__(self, other):
        return (">=", self, other)

    def __le__(self, other):
        return ("<=", self, other)

    def __eq__(self, other):
        return ("==", self, other)


class Variable:
    """Abstract variable class."""
    def __init__(self, name: str):
        self.name = name
        self.X = 0.0  # Solution value

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name
        return ("==", self, other)

    def __add__(self, other):
        result = LinearExpression()
        result.add_term(1.0, self.name)

        if isinstance(other, Variable):
            result.add_term(1.0, other.name)
        elif isinstance(other, LinearExpression):
            for var_name, coeff in other.terms.items():
                result.add_term(coeff, var_name)
            result.add_constant(other.constant)
        elif isinstance(other, (int, float)):
            result.add_constant(other)

        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            result = LinearExpression()
            result.add_term(other, self.name)
            return result
        else:
            raise TypeError("Can only multiply Variable by scalar")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __ge__(self, other):
        return (">=", self, other)

    def __le__(self, other):
        return ("<=", self, other)


class TupleDict:
    """Dictionary-like container for variables."""
    def __init__(self, variables: Dict[Any, Variable]):
        self._vars = variables

    def __getitem__(self, key):
        return self._vars[key]

    def __iter__(self):
        return iter(self._vars)

    def __len__(self):
        return len(self._vars)

    def keys(self):
        return self._vars.keys()

    def values(self):
        return self._vars.values()

    def items(self):
        return self._vars.items()


class SolverInterface(ABC):
    """Abstract base class for solver interfaces."""

    # Status constants
    OPTIMAL = "OPTIMAL"
    INFEASIBLE = "INFEASIBLE"
    UNBOUNDED = "UNBOUNDED"

    # Variable types
    BINARY = "BINARY"
    INTEGER = "INTEGER"
    CONTINUOUS = "CONTINUOUS"

    # Objective sense
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"

    def __init__(self, name: str = "model"):
        self.name = name
        self.status = None
        self.objVal = None

    @abstractmethod
    def addVar(self, vtype=CONTINUOUS, lb=0.0, ub=float('inf'), name="") -> Variable:
        pass

    @abstractmethod
    def addVars(self, *indices, vtype=CONTINUOUS, lb=0.0, ub=float('inf'), name="") -> TupleDict:
        pass

    @abstractmethod
    def addConstr(self, expr, name=""):
        pass

    @abstractmethod
    def addConstrs(self, generator, name=""):
        pass

    @abstractmethod
    def addMConstr(self, A, x, sense, b, name=""):
        pass

    @abstractmethod
    def setObjective(self, expr, sense=MINIMIZE):
        pass

    @abstractmethod
    def setParam(self, param, value):
        pass

    @abstractmethod
    def optimize(self):
        pass

    @abstractmethod
    def getVars(self) -> List[Variable]:
        pass

    @abstractmethod
    def quicksum(self, items):
        pass


class GurobiInterface(SolverInterface):
    """Gurobi solver interface."""

    def __init__(self, name: str = "gurobi_model"):
        super().__init__(name)
        try:
            import gurobipy as grb
            self.grb = grb
            self.model = grb.Model(name)
            self._variables = []  # Keep track of our Variable objects
            # Map our constants to Gurobi's
            self.OPTIMAL = grb.GRB.OPTIMAL
            self.INFEASIBLE = grb.GRB.INFEASIBLE
            self.UNBOUNDED = grb.GRB.UNBOUNDED
            self.BINARY = grb.GRB.BINARY
            self.INTEGER = grb.GRB.INTEGER
            self.CONTINUOUS = grb.GRB.CONTINUOUS
            self.MINIMIZE = grb.GRB.MINIMIZE
            self.MAXIMIZE = grb.GRB.MAXIMIZE
        except ImportError:
            raise SolverError("Gurobi not available. Install gurobipy or use a different solver.")

    def addVar(self, vtype=None, lb=0.0, ub=float('inf'), name="") -> Variable:
        if vtype is None:
            vtype = self.CONTINUOUS

        # Map our global constants to actual Gurobi constants
        vtype_map = {
            SolverInterface.BINARY: self.grb.GRB.BINARY,
            SolverInterface.INTEGER: self.grb.GRB.INTEGER,
            SolverInterface.CONTINUOUS: self.grb.GRB.CONTINUOUS
        }
        grb_vtype = vtype_map.get(vtype, vtype)

        grb_var = self.model.addVar(vtype=grb_vtype, lb=lb, ub=ub, name=name)
        # Update model to assign variable names
        self.model.update()
        var = Variable(grb_var.VarName)
        var._grb_var = grb_var  # Store reference to Gurobi variable
        self._variables.append(var)  # Register the variable
        return var

    def addVars(self, *indices, vtype=None, lb=0.0, ub=float('inf'), name="") -> TupleDict:
        if vtype is None:
            vtype = self.CONTINUOUS

        # Map our global constants to actual Gurobi constants
        vtype_map = {
            SolverInterface.BINARY: self.grb.GRB.BINARY,
            SolverInterface.INTEGER: self.grb.GRB.INTEGER,
            SolverInterface.CONTINUOUS: self.grb.GRB.CONTINUOUS
        }
        grb_vtype = vtype_map.get(vtype, vtype)

        if len(indices) == 1 and isinstance(indices[0], int):
            grb_vars = self.model.addVars(indices[0], vtype=grb_vtype, lb=lb, ub=ub, name=name if name else None)
        else:
            grb_vars = self.model.addVars(*indices, vtype=grb_vtype, lb=lb, ub=ub, name=name if name else None)

        # Update model to assign variable names
        self.model.update()

        variables = {}
        for key, grb_var in grb_vars.items():
            var = Variable(grb_var.VarName)
            var._grb_var = grb_var
            self._variables.append(var)  # Register the variable
            variables[key] = var

        return TupleDict(variables)

    def addConstr(self, expr, name=""):
        # Convert our constraint tuple to Gurobi constraint expression
        if isinstance(expr, tuple) and len(expr) == 3:
            sense, lhs, rhs = expr

            # Convert LinearExpression to Gurobi expression
            if isinstance(lhs, LinearExpression):
                lhs = self._convert_linear_expr_to_gurobi(lhs)
            elif hasattr(lhs, '_grb_var'):
                lhs = lhs._grb_var

            if isinstance(rhs, LinearExpression):
                rhs = self._convert_linear_expr_to_gurobi(rhs)
            elif hasattr(rhs, '_grb_var'):
                rhs = rhs._grb_var

            # Create Gurobi constraint expression
            if sense == ">=":
                expr = lhs >= rhs
            elif sense == "<=":
                expr = lhs <= rhs
            elif sense == "==":
                expr = lhs == rhs

        self.model.addConstr(expr, name=name)

    def _convert_linear_expr_to_gurobi(self, linear_expr):
        """Convert LinearExpression to Gurobi expression."""
        grb_expr = 0
        for var_name, coeff in linear_expr.terms.items():
            # Find the Gurobi variable by name
            for var in self.model.getVars():
                if var.VarName == var_name:
                    grb_expr += coeff * var
                    break
        grb_expr += linear_expr.constant
        return grb_expr

    def addConstrs(self, generator, name=""):
        # Convert our constraint tuples to Gurobi constraint expressions
        def convert_constraint(constraint):
            if isinstance(constraint, tuple) and len(constraint) == 3:
                sense, lhs, rhs = constraint
                # Convert our Variable objects to Gurobi variables
                if hasattr(lhs, '_grb_var'):
                    lhs = lhs._grb_var
                if hasattr(rhs, '_grb_var'):
                    rhs = rhs._grb_var

                # Return Gurobi constraint expression
                if sense == ">=":
                    return lhs >= rhs
                elif sense == "<=":
                    return lhs <= rhs
                elif sense == "==":
                    return lhs == rhs
            else:
                # Assume it's already a proper constraint
                return constraint

        # Convert generator to Gurobi constraints
        gurobi_generator = (convert_constraint(c) for c in generator)
        self.model.addConstrs(gurobi_generator, name=name)

    def addMConstr(self, A, x, sense, b, name=""):
        self.model.addMConstr(A=A, x=x, sense=sense, b=b, name=name)

    def setObjective(self, expr, sense=None):
        if sense is None:
            sense = self.MINIMIZE

        # Convert LinearExpression to Gurobi expression
        if isinstance(expr, LinearExpression):
            expr = self._convert_linear_expr_to_gurobi(expr)

        # Map our constants to Gurobi constants
        sense_map = {
            SolverInterface.MINIMIZE: self.grb.GRB.MINIMIZE,
            SolverInterface.MAXIMIZE: self.grb.GRB.MAXIMIZE
        }
        grb_sense = sense_map.get(sense, sense)

        self.model.setObjective(expr, grb_sense)

    def setParam(self, param, value):
        self.model.setParam(param, value)

    def optimize(self):
        self.model.optimize()
        self.status = self.model.status
        if self.status == self.OPTIMAL:
            self.objVal = self.model.objVal
            # Update solution values in our Variable objects
            for var in self.model.getVars():
                # Find corresponding Variable object and update X by comparing variable names
                for v in self.getVars():
                    if hasattr(v, '_grb_var') and v._grb_var.VarName == var.VarName:
                        v.X = var.X
                        break

    def getVars(self) -> List[Variable]:
        return self._variables

    def quicksum(self, items):
        return self.grb.quicksum(items)


class CBCInterface(SolverInterface):
    """CBC solver interface using PuLP."""

    def __init__(self, name: str = "cbc_model"):
        super().__init__(name)
        try:
            import pulp

            self.pulp = pulp
            self.model = pulp.LpProblem(name, pulp.LpMinimize)
            self.variables = {}
            self.constraints = []
            self.objective = None
            self.obj_sense = self.MINIMIZE
            self._pulp_vars = {}  # Store PuLP variables

        except ImportError as e:
            raise SolverError(f"CBC/PuLP not available: {e}. Install pulp or use a different solver.")

    def addVar(self, vtype=None, lb=0.0, ub=float('inf'), name="") -> Variable:
        if vtype is None:
            vtype = self.CONTINUOUS

        if not name:
            name = f"x{len(self.variables)}"

        # Create PuLP variable
        if vtype == self.BINARY:
            pulp_var = self.pulp.LpVariable(name, cat='Binary')
        elif vtype == self.INTEGER:
            if ub == float('inf'):
                pulp_var = self.pulp.LpVariable(name, lowBound=lb, cat='Integer')
            else:
                pulp_var = self.pulp.LpVariable(name, lowBound=lb, upBound=ub, cat='Integer')
        else:  # CONTINUOUS
            if ub == float('inf'):
                pulp_var = self.pulp.LpVariable(name, lowBound=lb)
            else:
                pulp_var = self.pulp.LpVariable(name, lowBound=lb, upBound=ub)

        var = Variable(name)
        var._pulp_var = pulp_var
        var._vtype = vtype
        self.variables[name] = var
        self._pulp_vars[name] = pulp_var

        return var

    def addVars(self, *indices, vtype=None, lb=0.0, ub=float('inf'), name="") -> TupleDict:
        if vtype is None:
            vtype = self.CONTINUOUS

        variables = {}

        if len(indices) == 1 and isinstance(indices[0], int):
            # Single integer - create variables indexed 0 to n-1
            n = indices[0]
            for i in range(n):
                var_name = f"{name}_{i}" if name else f"x{len(self.variables) + i}"
                var = self.addVar(vtype=vtype, lb=lb, ub=ub, name=var_name)
                variables[i] = var
        else:
            # Multiple indices
            index_list = indices[0] if hasattr(indices[0], '__iter__') else indices
            for idx in index_list:
                var_name = f"{name}_{idx}" if name else f"x{len(self.variables)}"
                var = self.addVar(vtype=vtype, lb=lb, ub=ub, name=var_name)
                variables[idx] = var

        return TupleDict(variables)

    def addConstr(self, expr, name=""):
        # Handle different types of constraint expressions
        if isinstance(expr, tuple) and len(expr) == 3:
            # Constraint tuple: (sense, lhs, rhs)
            sense, lhs, rhs = expr

            # Convert to standard form: lhs - rhs sense 0
            constraint_expr = LinearExpression()

            # Add LHS terms
            if isinstance(lhs, Variable):
                constraint_expr.add_term(1.0, lhs.name)
            elif isinstance(lhs, LinearExpression):
                for var_name, coeff in lhs.terms.items():
                    constraint_expr.add_term(coeff, var_name)
                constraint_expr.add_constant(lhs.constant)

            # Subtract RHS terms
            if isinstance(rhs, Variable):
                constraint_expr.add_term(-1.0, rhs.name)
            elif isinstance(rhs, LinearExpression):
                for var_name, coeff in rhs.terms.items():
                    constraint_expr.add_term(-coeff, var_name)
                constraint_expr.add_constant(-rhs.constant)
            elif isinstance(rhs, (int, float)):
                constraint_expr.add_constant(-rhs)

            constraint = {
                'expr': constraint_expr,
                'sense': sense,
                'rhs': 0.0,  # Standard form: lhs - rhs sense 0
                'name': name
            }
            self.constraints.append(constraint)
        else:
            # Simple constraint
            self.constraints.append((expr, name))

    def addConstrs(self, generator, name=""):
        for i, constr in enumerate(generator):
            constraint_name = f"{name}_{i}" if name else f"constr_{len(self.constraints)}"
            self.addConstr(constr, name=constraint_name)

    def addMConstr(self, A, x, sense, b, name=""):
        # Convert sparse matrix constraints to individual linear constraints
        if hasattr(A, 'tocoo'):
            A_coo = A.tocoo()
        else:
            A_coo = A

        # Get all variables in order: x, y, z
        all_vars = list(self.variables.values())

        # Convert each row of the matrix to a linear constraint
        for row_idx in range(A_coo.shape[0]):
            constraint_expr = LinearExpression()

            # Extract non-zero elements from this row
            if hasattr(A_coo, 'row'):  # COO format
                row_mask = A_coo.row == row_idx
                cols = A_coo.col[row_mask]
                data = A_coo.data[row_mask]
            else:  # Dense or other format
                row = A_coo[row_idx]
                cols = []
                data = []
                for col_idx, val in enumerate(row):
                    if abs(val) > 1e-10:
                        cols.append(col_idx)
                        data.append(val)

            # Add terms to constraint expression
            for col_idx, coeff in zip(cols, data):
                if col_idx < len(all_vars):
                    constraint_expr.add_term(float(coeff), all_vars[col_idx].name)

            # Get constraint sense and RHS
            row_sense = sense[row_idx] if isinstance(sense, list) else sense
            row_rhs = float(b[row_idx]) if hasattr(b, '__getitem__') else float(b)

            # Convert to standard form (lhs - rhs >= 0)
            constraint_expr.add_constant(-row_rhs)

            # Create constraint dictionary
            constraint = {
                'expr': constraint_expr,
                'sense': row_sense,
                'rhs': 0.0,  # Standard form
                'name': f"{name}_{row_idx}" if name else f"matrix_constr_{row_idx}"
            }
            self.constraints.append(constraint)

    def setObjective(self, expr, sense=None):
        if sense is None:
            sense = self.MINIMIZE
        self.objective = expr
        self.obj_sense = sense

        # Convert our expression to PuLP format
        pulp_expr = self._convert_to_pulp_expr(expr)

        if sense == self.MINIMIZE:
            self.model.sense = self.pulp.LpMinimize
        else:
            self.model.sense = self.pulp.LpMaximize

        self.model.setObjective(pulp_expr)

    def setParam(self, param, value):
        # CBC parameters would be set differently
        # This is a placeholder
        pass

    def optimize(self):
        try:
            # Add constraints to PuLP model
            for constraint in self.constraints:
                if isinstance(constraint, dict) and 'expr' in constraint:
                    pulp_constraint = self._convert_constraint_to_pulp(constraint)
                    self.model += pulp_constraint

            # Solve using CBC
            solver = self.pulp.PULP_CBC_CMD(msg=False)
            self.model.solve(solver)

            # Check status
            if self.model.status == self.pulp.LpStatusOptimal:
                self.status = self.OPTIMAL
                self.objVal = self.pulp.value(self.model.objective)

                # Update variable solution values
                for var in self.variables.values():
                    if hasattr(var, '_pulp_var'):
                        var.X = self.pulp.value(var._pulp_var)
            elif self.model.status == self.pulp.LpStatusInfeasible:
                self.status = self.INFEASIBLE
            elif self.model.status == self.pulp.LpStatusUnbounded:
                self.status = self.UNBOUNDED
            else:
                self.status = self.INFEASIBLE

        except Exception as e:
            raise SolverError(f"CBC optimization failed: {e}")

    def getVars(self) -> List[Variable]:
        return list(self.variables.values())

    def quicksum(self, items):
        # Proper quicksum implementation for LinearExpressions
        result = LinearExpression()
        for item in items:
            if isinstance(item, Variable):
                result.add_term(1.0, item.name)
            elif isinstance(item, LinearExpression):
                for var_name, coeff in item.terms.items():
                    result.add_term(coeff, var_name)
                result.add_constant(item.constant)
            elif isinstance(item, (int, float)):
                result.add_constant(item)
        return result

    def _convert_to_pulp_expr(self, expr):
        """Convert our expression format to PuLP format."""
        if isinstance(expr, Variable):
            return self._pulp_vars[expr.name]
        elif isinstance(expr, LinearExpression):
            pulp_expr = 0
            for var_name, coeff in expr.terms.items():
                pulp_expr += coeff * self._pulp_vars[var_name]
            pulp_expr += expr.constant
            return pulp_expr
        elif isinstance(expr, (int, float)):
            return expr
        else:
            # Try to handle other expression types
            return expr

    def _convert_constraint_to_pulp(self, constraint):
        """Convert constraint dict to PuLP constraint."""
        expr = constraint['expr']
        sense = constraint['sense']

        # Convert expression to PuLP format
        pulp_expr = 0
        for var_name, coeff in expr.terms.items():
            pulp_expr += coeff * self._pulp_vars[var_name]

        # Apply sense and RHS
        rhs = -expr.constant  # Move constant to RHS

        if sense == ">=" or sense == ">":
            return pulp_expr >= rhs
        elif sense == "<=" or sense == "<":
            return pulp_expr <= rhs
        elif sense == "==" or sense == "=":
            return pulp_expr == rhs
        else:
            raise ValueError(f"Unknown constraint sense: {sense}")


def create_solver(solver_type: str = "auto", **kwargs) -> SolverInterface:
    """
    Create a solver interface.

    Args:
        solver_type: "gurobi", "cbc", or "auto" (tries gurobi first, falls back to cbc)
        **kwargs: Additional arguments passed to solver constructor

    Returns:
        SolverInterface instance
    """
    if solver_type == "auto":
        # Try Gurobi first, fall back to CBC
        try:
            return GurobiInterface(**kwargs)
        except SolverError:
            try:
                return CBCInterface(**kwargs)
            except SolverError:
                raise SolverError("Neither Gurobi nor CBC are available")

    elif solver_type == "gurobi":
        return GurobiInterface(**kwargs)

    elif solver_type == "cbc":
        return CBCInterface(**kwargs)

    else:
        raise ValueError(f"Unknown solver type: {solver_type}. Use 'gurobi', 'cbc', or 'auto'")


# Backwards compatibility aliases
def Model(name="model", solver="auto"):
    """Create a model using specified solver."""
    return create_solver(solver, name=name)


def quicksum(items, solver=None):
    """Quicksum function - if solver is provided, use its implementation."""
    if solver:
        return solver.quicksum(items)
    else:
        # Fallback implementation
        result = 0
        for item in items:
            result += item
        return result


# Constants for backwards compatibility
class GRB:
    BINARY = SolverInterface.BINARY
    INTEGER = SolverInterface.INTEGER
    CONTINUOUS = SolverInterface.CONTINUOUS
    MINIMIZE = SolverInterface.MINIMIZE
    MAXIMIZE = SolverInterface.MAXIMIZE
    OPTIMAL = SolverInterface.OPTIMAL
    INFEASIBLE = SolverInterface.INFEASIBLE
    UNBOUNDED = SolverInterface.UNBOUNDED