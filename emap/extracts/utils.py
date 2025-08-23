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


def normalized_to_json(inputs: dict[str, list[int]], outputs: dict[str, list[int]], cells: list[dict[str, Any]], dffs: list[dict[str, Any]]) -> dict:
    """
    Convert normalized representation to Yosys JSON format.
    """
    # TODO: implement this function
    return {}