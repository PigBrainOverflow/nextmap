from ..db import NetlistDB
import gurobipy


def _group_wires(wires: list[set[str]]):
    

def extract_dsps(db: NetlistDB, cost_model) -> dict:
    ilp_model = gurobipy.Model("egraph_extraction")

    x = ilp_model.addVars()