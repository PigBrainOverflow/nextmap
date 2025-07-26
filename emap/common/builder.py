from typing import Any


def bit_to_int(bit: str | int) -> int:
    return -1 if bit == "x" else int(bit)

def json_to_db(mod: dict[str, Any]) -> dict[str, Any]:
    ports: dict = mod["ports"]
    cells: dict = mod["cells"]
    global_clk = -1

    # build ports
    db_inputs: dict[int, str] = {}
    db_outputs: dict[int, str] = {}
    for name, port in ports.items():
        bits, direction = port["bits"], port["direction"]
        if direction == "input":
            db_inputs.update((bit_to_int(bit), f"{name}[{i}]") for i, bit in enumerate(bits))
        elif direction == "output":
            db_outputs.update((bit_to_int(bit), f"{name}[{i}]") for i, bit in enumerate(bits))
        else:
            raise ValueError(f"Unsupported port direction: {direction}")

    # build cells
    db_arith_cells: list[tuple[str, bool, list[int], list[int], list[int]]] = []
    db_logic_ay_cells: list[tuple[str, list[int], list[int]]] = []
    db_logic_aby_cells: list[tuple[str, list[int], list[int], list[int]]] = []
    db_muxes: list[tuple[list[int], list[int], int, list[int]]] = []
    db_dffs: list[tuple[list[int], list[int]]] = []
    for cell in cells.values():
        type_ = cell["type"]
        if type_ in {"$add", "$sub", "$mul", "$mod"}:  # db_arith_cells
            params = cell["parameters"]
            db_arith_cells.append((
                type_,
                bool(int(params["A_SIGNED"], base=2)) and bool(int(params["B_SIGNED"], base=2)),
                list(map(bit_to_int, cell["connections"]["A"])),
                list(map(bit_to_int, cell["connections"]["B"])),
                list(map(bit_to_int, cell["connections"]["Y"])),
            ))
        elif type_ in {"$not", "$logic_not"}:   # db_logic_ay_cells
            db_logic_ay_cells.append((
                type_,
                list(map(bit_to_int, cell["connections"]["A"])),
                list(map(bit_to_int, cell["connections"]["Y"]))
            ))
        elif type_ in {
            "$and", "$or", "$xor", "$logic_and", "$logic_or",
            "$eq", "$ne", "$ge", "$le", "$gt", "$lt"
        }:    # db_logic_aby_cells
            db_logic_aby_cells.append((
                type_,
                list(map(bit_to_int, cell["connections"]["A"])),
                list(map(bit_to_int, cell["connections"]["B"])),
                list(map(bit_to_int, cell["connections"]["Y"]))
            ))
        elif type_ == "$mux":  # db_muxes
            if len(cell["connections"]["S"]) != 1:
                raise ValueError("Only single-bit select signal is supported for $mux")
            db_muxes.append((
                list(map(bit_to_int, cell["connections"]["A"])),
                list(map(bit_to_int, cell["connections"]["B"])),
                bit_to_int(cell["connections"]["S"][0]),
                list(map(bit_to_int, cell["connections"]["Y"]))
            ))
        elif type_ == "$dff":  # db_dffs
            params = cell["parameters"]
            if not bool(int(params["CLK_POLARITY"], base=2)):
                raise ValueError("$dff with negative clock polarity is not supported")
            if len(cell["connections"]["CLK"]) != 1:
                raise ValueError("Only single-bit clock is supported for $dff")
            clk = bit_to_int(cell["connections"]["CLK"][0])
            if global_clk == -1:
                global_clk = clk
            elif global_clk != clk:
                raise ValueError("Multiple clock signals found in the design")
            db_dffs.append((
                list(map(bit_to_int, cell["connections"]["D"])),
                list(map(bit_to_int, cell["connections"]["Q"]))
            ))
        else:
            attrs = cell["attributes"]
            if "module_not_derived" in attrs and bool(int(attrs["module_not_derived"], base=2)):    # blackbox cell
                raise ValueError(f"Blackbox is not supported")
            else:
                raise ValueError(f"Unsupported cell type: {type_}")

    return {
        "inputs": db_inputs,
        "outputs": db_outputs,
        "global_clk": global_clk,
        "arith_cells": db_arith_cells,
        "logic_ay_cells": db_logic_ay_cells,
        "logic_aby_cells": db_logic_aby_cells,
        "muxes": db_muxes,
        "dffs": db_dffs
    }

def build_and_sanitize_db_fast(mod_db: dict[str, Any]):
    from ..cpp.build import emapcc
    ay_cells, aby_cells, absy_cells, dffs = emapcc.build_and_sanitize_db(
        [input for input in mod_db["inputs"]],
        [output for output in mod_db["outputs"]],
        mod_db["arith_cells"],
        mod_db["logic_ay_cells"],
        mod_db["logic_aby_cells"],
        mod_db["muxes"],
        mod_db["dffs"]
    )   # TODO