from typing import Any
import itertools
from ..db import NetlistDB


# NOTE: It works like a recursive descent parser, except that it returns multiple matches.
# It also looks ahead when necessary.
def match_dsp(db: NetlistDB, a: int, b: int, y: int) -> dict[str, Any]:
    return {
        "type": "dsp",
        # two pre-mult stages
        "a_pre_mult": match_dsp_a_pre_mult(db, a),
        "b_pre_mult": match_wire_or_reg(db, b),
        # one post-mult stage
        "post_mult": match_dsp_post_mult(db, y)
    }

def match_wire_or_reg(db: NetlistDB, w: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    # case 1: w comes from a wire
    matches.append({"type": "wire", "inputs": {"": w}})
    # case 2: w comes from a dff or sdff
    matches.extend(match_dff_or_sdff(db, w))
    return matches

def match_dff_or_sdff(db: NetlistDB, q: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    cur = db.execute("SELECT d FROM dffs WHERE q = %s", (q,))
    for (d,) in cur.fetchall():
        # case 1: d comes from a wire, so this is a dff
        matches.append({"type": "dff", "inputs": {"D": d}})
        # case 2: d comes from a mux of a wire and constant 0, so this is a sdff
        cur = db.execute("SELECT a, b, s FROM absy_cells WHERE type = '$mux' AND y = %s", (d,))
        for a, b, s in cur:
            bwv = db._get_wirevec(b)
            if all(bit == 0 for bit in bwv):
                matches.append({"type": "sdff", "inputs": {"D": a, "RST": s}})
    return matches

def match_dsp_a_pre_mult(db: NetlistDB, a: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    # case 1: a comes from a wire or reg
    matches.extend(match_wire_or_reg(db, a))
    # case 2: a comes from an add
    cur = db.execute("SELECT a, b FROM aby_cells WHERE type = '$adds' AND y = %s AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = a) <= 26 AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = b) <= 18", (a,))
    for add_a, add_b in cur:
        matches.append({
            "type": "add",
            "a": match_wire_or_reg(db, add_a),
            "d": match_wire_or_reg(db, add_b)
        })
    # case 3: a comes from a sub
    cur = db.execute("SELECT a, b FROM aby_cells WHERE type = '$subs' AND y = %s AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = a) <= 26 AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = b) <= 18", (a,))
    for sub_a, sub_b in cur:
        matches.append({
            "type": "sub",
            "a": match_wire_or_reg(db, sub_a),
            "d": match_wire_or_reg(db, sub_b)
        })
    return matches

def match_dsp_post_mult(db: NetlistDB, y: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    # case 1: y goes to a wire
    matches.extend(match_dsp_post_mult_op(db, y))
    # case 2: y goes to a dff
    cur = db.execute("SELECT q FROM dffs WHERE d = %s", (y,))
    for (q,) in cur:
        matches.extend(match_dsp_post_mult_op(db, q))
    return matches

def match_dsp_post_mult_op(db: NetlistDB, w: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    # case 1: no op
    matches.append({"type": "none", "outputs": {"P": w}})
    # case 2: w goes to an add
    cur = db.execute("SELECT b, y FROM aby_cells WHERE type = '$adds' AND a = %s AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = b) <= 48", (w,))
    for add_b, add_y in cur:
        matches.append({
            "type": "add",
            "c_pre_mult": match_wire_or_reg(db, add_b),
            "outputs": {"P": add_y}
        })
    # case 3: w goes to a sub
    cur = db.execute("SELECT b, y FROM aby_cells WHERE type = '$subs' AND a = %s AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = b) <= 48", (w,))
    for sub_b, sub_y in cur:
        matches.append({
            "type": "sub",
            "c_pre_mult": match_wire_or_reg(db, sub_b),
            "outputs": {"P": sub_y}
        })
    return matches

def expand(db: NetlistDB, match: dict[str, Any]) -> list[tuple[set[int], set[int]]]:
    # return a list of (inputs, outputs)
    res: list[tuple[set[int], set[int]]] = []
    inputs: set[int] = set()
    outputs: set[int] = set()
    # direct inputs/outputs
    for input in match.get("inputs", {}).values():
        inputs.update(db._get_wirevec(input))
    for output in match.get("outputs", {}).values():
        outputs.update(db._get_wirevec(output))
    # recursively expand children
    children: list[list[tuple[set[int], set[int]]]] = []
    # if match["type"] in {"add", "sub"}:
    #     print("found add/sub")
    for name, child in match.items():
        if name not in {"type", "inputs", "outputs"}:
            if isinstance(child, list):
                children.append([item for c in child for item in expand(db, c)])
            else:
                children.append(expand(db, child))
    for tup in itertools.product(*children):
        tmp_inputs, tmp_outputs = set(inputs), set(outputs)
        for child in tup:
            tmp_inputs.update(child[0])
            tmp_outputs.update(child[1])
        res.append((tmp_inputs, tmp_outputs))
    return res

def techmap_dsp(db: NetlistDB):
    # basis: multiplication
    cur = db.execute("""
        SELECT a, b, y FROM aby_cells
        WHERE type = '$muls' AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = a) <= 27 AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = b) <= 18 AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = y) <= 48
    """)
    matches = []
    for a, b, y in cur:
        matches.append(match_dsp(db, a, b, y))

    # expand matches and insert into db
    for match in matches:
        db.executemany(
            "INSERT INTO tech_dsp_generic (inputs, outputs) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            ((db._create_or_lookup_wirevec(sorted(inputs)), db._create_or_lookup_wirevec(sorted(outputs)))
            for inputs, outputs in expand(db, match))
        )