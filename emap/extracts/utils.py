from ..db import NetlistDB
from typing import Callable, Any


def db_to_normalized(db: NetlistDB, cost_model: Callable) -> tuple[dict[str, list[int]], dict[str, list[int]], list[dict[str, Any]]]:
    """
    Return (inputs, outputs, cells & dffs) where cells & dffs is a list of dicts with keys "cost", "type", "inputs", "outputs":
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
        "type": "$dff",
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
    cur = db.execute("SELECT UNIQUE id FROM wirevecs")
    for (wirevec_id,) in cur.fetchall():
        cur.execute("SELECT bit FROM wirevec_bits WHERE wirevec_id = ? ORDER BY bit_index", (wirevec_id,))
        wirevecs[wirevec_id] = [bit for (bit,) in cur]

    # normalize inputs
    inputs = {}
