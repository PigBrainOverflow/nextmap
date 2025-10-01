from ..db import NetlistDB


def techmap_lut(netlist: NetlistDB, k: int, cnt: int, rseed: int):
    """
    Techmap the netlist to k-LUTs
    """
    if netlist.VERBOSE:
        print(f"Techmapping to {k}-LUTs with random seed {rseed}")
    