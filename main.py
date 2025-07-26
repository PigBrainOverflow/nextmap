import json
from emap.common import json_to_db


if __name__ == "__main__":
    with open("tests/designs/systolic/systolic.json", "r") as f:
        design = json.load(f)
    db_inputs, db_outputs, global_clk, db_arith_cells, db_logic_ay_cells, db_logic_aby_cells, db_muxes, db_dffs = json_to_db(design["modules"]["systolic"])
    
    with open("systolic_db.json", "w") as f:
        json.dump({
            "inputs": db_inputs,
            "outputs": db_outputs,
            "global_clk": global_clk,
            "arith_cells": db_arith_cells,
            "logic_ay_cells": db_logic_ay_cells,
            "logic_aby_cells": db_logic_aby_cells,
            "muxes": db_muxes,
            "dffs": db_dffs
        }, f, indent=4)