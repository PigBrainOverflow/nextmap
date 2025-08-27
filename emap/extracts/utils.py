from ..db import NetlistDB
from typing import Callable, Any


def db_to_normalized(db: NetlistDB, cost_model: Callable) -> tuple[dict[str, list[int]], dict[str, list[int]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Return (inputs, outputs, cells, dffs) where cells and dffs are lists of dicts with keys "cost", "type", "inputs", "outputs":
    {
        "cost": 5,
        "type": "$and",
        "inputs": {
            "a": [1, 2],
            "b": [3, 4]
        },
        "outputs": {
            "y": [5, 6]
        }
    }
    {
        "cost": 10,
        "inputs": {
            "d": [1, 2]
        },
        "outputs": {
            "q": [3, 4]
        }
    }
    NOTE: There is no "clk" field in dffs since we assume there's a global clock.
    """
    # read all wirevecs
    wirevecs: dict[int, list[int]] = {}
    cur = db.execute("SELECT id FROM wirevecs")
    for (id,) in cur.fetchall():
        cur.execute("SELECT wire FROM wirevec_members WHERE wirevec = ? ORDER BY idx", (id,))
        wirevecs[id] = [wire for (wire,) in cur]

    # normalize inputs
    inputs: dict[str, list[int]] = {}
    cur = db.execute("SELECT source, name FROM from_inputs")
    for source, name in cur:
        assert name not in inputs
        inputs[name] = wirevecs[source]

    # normalize outputs
    outputs: dict[str, list[int]] = {}
    cur = db.execute("SELECT sink, name FROM as_outputs")
    for sink, name in cur:
        assert name not in outputs
        outputs[name] = wirevecs[sink]

    # normalize cells & dffs
    cells: list[dict[str, Any]] = []
    dffs: list[dict[str, Any]] = []
    cur = db.execute("SELECT type, a, y FROM ay_cells")
    for type_, a, y in cur:
        a, y = wirevecs[a], wirevecs[y]
        cells.append({
            "cost": cost_model(type_, a, y),
            "type": type_,
            "inputs": {"a": a},
            "outputs": {"y": y}
        })

    cur = db.execute("SELECT type, a, b, y FROM aby_cells")
    for type_, a, b, y in cur:
        a, b, y = wirevecs[a], wirevecs[b], wirevecs[y]
        cells.append({
            "cost": cost_model(type_, a, b, y),
            "type": type_,
            "inputs": {"a": a, "b": b},
            "outputs": {"y": y}
        })

    cur = db.execute("SELECT type, a, b, s, y FROM absy_cells")
    for type_, a, b, s, y in cur:
        a, b, s, y = wirevecs[a], wirevecs[b], wirevecs[s], wirevecs[y]
        cells.append({
            "cost": cost_model(type_, a, b, s, y),
            "type": type_,
            "inputs": {"a": a, "b": b, "s": s},
            "outputs": {"y": y}
        })

    cur = db.execute("SELECT d, q FROM dffs")
    for d, q in cur:
        d, q = wirevecs[d], wirevecs[q]
        dffs.append({
            "cost": cost_model("$dff", d, q),
            "inputs": {"d": d},
            "outputs": {"q": q}
        })

    cur = db.execute("SELECT * FROM instances LIMIT 1")
    if cur.fetchone() is not None:
        raise ValueError("Blackbox instances are not supported in the current version of Nextmap.")

    return inputs, outputs, cells, dffs


def db_to_normalized_tech(db: NetlistDB, cost_model: Callable, tech_rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return a list of tech cells in the same format as in db_to_normalized.
    """
    # read all wirevecs
    wirevecs: dict[int, list[int]] = {}
    cur = db.execute("SELECT id FROM wirevecs")
    for (id,) in cur.fetchall():
        cur.execute("SELECT wire FROM wirevec_members WHERE wirevec = ? ORDER BY idx", (id,))
        wirevecs[id] = [wire for (wire,) in cur]

    tech_cells: list[dict[str, Any]] = []
    for name, rule in tech_rules.items():
        inputs_ports = rule["inputs"]
        outputs_ports = rule["outputs"]
        cur = db.execute(f"SELECT {', '.join(inputs_ports + outputs_ports)} FROM tech_{name}")
        for row in cur:
            inputs = {port: wirevecs[row[i]] for i, port in enumerate(inputs_ports)}
            outputs = {port: wirevecs[row[i + len(inputs_ports)]] for i, port in enumerate(outputs_ports)}
            tech_cells.append({
                "cost": cost_model(name, *inputs.values(), *outputs.values()),
                "type": name,
                "inputs": inputs,
                "outputs": outputs
            })
    return tech_cells


def cell_to_json(clk: int, tech_rules: dict[str, dict[str, Any]], cell: dict[str, Any]) -> dict[str, Any]:
    type_, inputs, outputs = cell["type"], cell["inputs"], cell["outputs"]
    if not type_.startswith("$"):   # tech cell
        tech_rule = tech_rules.get(type_)
        res = {
            # for simplicity, we omit signed/zero-extension
            "hide_name": 1,
            "type": type_,
            "parameters": {},
            "port_directions": {port: "input" for port in tech_rule["inputs"] + tech_rule["hidden_inputs"]} | {port: "output" for port in tech_rule["outputs"]},
            "connections": {port: inputs[port] for port in tech_rule["inputs"]} | {port: outputs[port] for port in tech_rule["outputs"]}
        }
        for hi in tech_rule["hidden_inputs"]:
            if hi != "clk":
                raise ValueError(f"Unsupported hidden input {hi} in tech cell {type_}")
            res["connections"][hi] = [clk]
        return res
    if len(inputs) == 1:
        return {
            "hide_name": 1,
            "type": type_,
            "parameters": {
                "A_SIGNED": 0,
                "A_WIDTH": len(inputs["a"]),
                "Y_WIDTH": len(outputs["y"])
            },
            "port_directions": {
                "A": "input",
                "Y": "output"
            },
            "connections": {
                "A": inputs["a"],
                "Y": outputs["y"]
            }
        }
    if len(inputs) == 2:
        res = {
            "hide_name": 1,
            "parameters": {
                "A_SIGNED": 0,
                "B_SIGNED": 0,
                "A_WIDTH": len(inputs["a"]),
                "B_WIDTH": len(inputs["b"]),
                "Y_WIDTH": len(outputs["y"])
            },
            "port_directions": {
                "A": "input",
                "B": "input",
                "Y": "output"
            },
            "connections": {
                "A": inputs["a"],
                "B": inputs["b"],
                "Y": outputs["y"]
            }
        }
        if type_.endswith(("s", "u")):
            is_signed = type_.endswith("s")
            res["type"] = type_[:-1]
            res["parameters"]["A_SIGNED"] = int(is_signed)
            res["parameters"]["B_SIGNED"] = int(is_signed)
        else:
            res["type"] = type_
        return res
    if len(inputs) == 3:
        return {
            "hide_name": 1,
            "type": type_,
            "parameters": {
                "WIDTH": len(inputs["a"])
            },
            "port_directions": {
                "A": "input",
                "B": "input",
                "S": "input",
                "Y": "output"
            },
            "connections": {
                "A": inputs["a"],
                "B": inputs["b"],
                "S": inputs["s"],
                "Y": outputs["y"]
            }
        }
    raise ValueError(f"Unsupported cell type: {type_}")

def dff_to_json(clk: int, dff: dict[str, Any]) -> dict[str, Any]:
    inputs, outputs = dff["inputs"], dff["outputs"]
    return {
        "hide_name": 1,
        "type": "$dff",
        "parameters": {
            "CLK_POLARITY": 1,
            "WIDTH": len(inputs["d"])
        },
        "port_directions": {
            "CLK": "input",
            "D": "input",
            "Q": "output"
        },
        "connections": {
            "CLK": [clk],
            "D": inputs["d"],
            "Q": outputs["q"]
        }
    }

def normalized_to_json(db: NetlistDB, tech_rules: dict[str, dict[str, Any]], inputs: dict[str, list[int]], outputs: dict[str, list[int]], cells: list[dict[str, Any]], dffs: list[dict[str, Any]]) -> dict:
    """
    Convert normalized representation to Yosys JSON format.
    """
    mod = {}

    # build ports
    mod["ports"] = {name: {"direction": "input", "bits": source} for name, source in inputs.items()}
    mod["ports"].update({name: {"direction": "output", "bits": sink} for name, sink in outputs.items()})

    # build cells
    mod["cells"] = {}
    for i, cell in enumerate(cells):
        mod["cells"][f"cell_{i}"] = cell_to_json(db._clk, tech_rules, cell)
    for i, dff in enumerate(dffs):
        mod["cells"][f"dff_{i}"] = dff_to_json(db._clk, dff)

    # TODO: build blackbox instances

    return mod