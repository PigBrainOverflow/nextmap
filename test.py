import emap
import json

SCHEMA_PATH = "emap/schema.sql"

def simple_cost_model(type_: str, *ports) -> float:
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

dsp_rules = {
    "signed_mul_1_stage_26_17_48_bit": {    # rule name
        "requirements": {                   # resource requirements
            "dsp48e2": 1                    # use one DSP48E2
        },
        "hidden_inputs": ["clk"],   # hidden input ports, e.g., clock
        "inputs": ["a", "b"],       # input ports
        "outputs": ["p"],           # output ports
        # and a match pattern in SQL
        "match_sql": """
            SELECT mul1.a, mul1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS mul1
            ON dff1.d = mul1.y
            WHERE mul1.type = '$muls'
                AND width_of(mul1.a) <= 26 AND width_of(mul1.b) <= 17 AND width_of(dff1.q) <= 48
        """
    },
    "signed_muladd_1_stage_26_17_48_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT mul1.a, mul1.b, add1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS mul1 JOIN aby_cells AS add1
            ON dff1.d = add1.y AND mul1.y = add1.a
            WHERE mul1.type = '$muls' AND add1.type = '$adds'
                AND width_of(mul1.a) <= 26 AND width_of(mul1.b) <= 17 AND width_of(add1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    },
    "unsigned_muladd_1_stage_27_18_48_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT mul1.a, mul1.b, add1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS mul1 JOIN aby_cells AS add1
            ON dff1.d = add1.y AND mul1.y = add1.a
            WHERE mul1.type = '$mulu' AND add1.type = '$addu'
                AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(add1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    },
    "signed_mulsub_1_stage_27_18_48_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT mul1.a, mul1.b, sub1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS mul1 JOIN aby_cells AS sub1
            ON dff1.d = sub1.y AND mul1.y = sub1.a
            WHERE mul1.type = '$muls' AND sub1.type = '$subs'
                AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(sub1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    },
    "signed_submuladd_1_stage_26_18_48_26_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["d", "a", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT sub1.a, sub1.b, mul1.b, add1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS sub1 JOIN aby_cells AS mul1 JOIN aby_cells AS add1
            ON dff1.d = add1.y AND sub1.y = mul1.a AND mul1.y = add1.a
            WHERE sub1.type = '$subs' AND mul1.type = '$muls' AND add1.type = '$adds'
                AND width_of(sub1.a) <= 26 AND width_of(sub1.b) <= 26 AND width_of(mul1.b) <= 18 AND width_of(add1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    },
    "signed_addmuladd_1_stage_26_18_48_26_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "d", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT add2.a, add2.b, mul1.b, add1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS add2 JOIN aby_cells AS mul1 JOIN aby_cells AS add1
            ON dff1.d = add1.y AND add2.y = mul1.a AND mul1.y = add1.a
            WHERE add2.type = '$adds' AND mul1.type = '$muls' AND add1.type = '$adds'
                AND width_of(add2.a) <= 26 AND width_of(add2.b) <= 26 AND width_of(mul1.b) <= 18 AND width_of(add1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    },
    "signed_submul_1_stage_27_18_48_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["d", "a", "b"],
        "outputs": ["p"],
        "match_sql": """
            SELECT sub1.a, sub1.b, mul1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS sub1 JOIN aby_cells AS mul1
            ON dff1.d = mul1.y AND sub1.y = mul1.a
            WHERE sub1.type = '$subs' AND mul1.type = '$muls'
                AND width_of(sub1.a) <= 27 AND width_of(sub1.b) <= 27 AND width_of(mul1.b) <= 18 AND width_of(dff1.q) <= 48
        """
    },
    "signed_mul_2_stage_26_17_48_bit_rst": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "rst"],
        "outputs": ["p"],
        "match_sql": """
            SELECT sdff_a.d, sdff_b.d, sdff_p.rst, sdff_p.q
            FROM sdffs AS sdff_a JOIN sdffs AS sdff_b JOIN aby_cells AS mul JOIN sdffs AS sdff_p
            ON sdff_a.q = mul.a AND sdff_b.q = mul.b AND mul.y = sdff_p.d
            WHERE mul.type = '$muls'
                AND width_of(sdff_a.d) <= 26 AND width_of(sdff_b.d) <= 17 AND width_of(sdff_p.q) <= 48
                AND sdff_a.rst = sdff_b.rst AND sdff_b.rst = sdff_p.rst
                AND sdff_a.rst_val = 0 AND sdff_b.rst_val = 0 AND sdff_p.rst_val = 0
        """
    },
    "signed_square_diff_1_stage_18_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "d"],
        "outputs": ["p"],
        "match_sql": """
            SELECT sub1.a, sub1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS sub1 JOIN aby_cells AS mul1
            ON dff1.d = mul1.y AND sub1.y = mul1.a AND sub1.y = mul1.b
            WHERE sub1.type = '$subs' AND mul1.type = '$muls'
                AND width_of(sub1.a) <= 18 AND width_of(sub1.b) <= 18 AND width_of(mul1.a) <= 18 AND width_of(dff1.q) <= 36
        """
    },
    "signed_mul_1_stage_27_18_48_bit_with_ab_out": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b"],
        "outputs": ["a_out", "b_out", "p"],
        "match_sql": """
            SELECT dff_a.d, dff_b.d, mul1.a, mul1.b, mul1.y
            FROM dffs AS dff_a JOIN dffs AS dff_b JOIN aby_cells AS mul1
            ON dff_a.q = mul1.a AND dff_b.q = mul1.b
            WHERE mul1.type = '$muls'
                AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(mul1.y) <= 48
        """
    },
    "signed_muladd_1_stage_27_18_48_bit_with_ab_out": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["a_out", "b_out", "p"],
        "match_sql": """
            SELECT dff_a.d, dff_b.d, add1.b, mul1.a, mul1.b, mul1.y
            FROM dffs AS dff_a JOIN dffs AS dff_b JOIN aby_cells AS mul1 JOIN aby_cells AS add1
            ON dff_a.q = mul1.a AND dff_b.q = mul1.b AND mul1.y = add1.a
            WHERE mul1.type = '$muls' AND add1.type = '$adds'
                AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(add1.b) <= 48 AND width_of(mul1.y) <= 48
        """
    }
}

TEST_NAME = "nerv"
netlist = emap.NetlistDB(SCHEMA_PATH)
with open(f"eval/out/{TEST_NAME}.json", "r") as f:
    netlist.build_from_json(json.load(f)["modules"]["nerv"], clk="clock")

netlist.rebuild()

cnt = 1
while cnt > 0:
    comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
    dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
    dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])

    cnt = emap.rewrites.apply_comm(netlist, comm_matches)
    cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)
    cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_aby_cell_matches)
    if cnt > 0:
        print(f"Applied {cnt} rewrites")
    else:
        print("No rewrites applied, stopping")
    netlist.rebuild()

# techmapping
emap.rewrites.create_tech_tables(netlist, dsp_rules)
emap.rewrites.rewrite_tech(netlist, dsp_rules)
mod = emap.extracts.ilp.extract_techmap_with_limit(netlist, simple_cost_model, dsp_rules, {"dsp48e2": 16}, OutputFlag=False)

with open(f"eval/out/{TEST_NAME}_extracted.json", "w") as f:
    json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)