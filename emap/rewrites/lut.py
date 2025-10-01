import random
from ..db import NetlistDB


def find_cone(netlist: NetlistDB, k: int, w: int) -> set[int]:
    # TODO: We can also add randomness here
    # WARNING: This is inefficient since we don't cache the frontier
    cone: set[int] = {w}
    # BFS from w
    while len(cone) < k:
        # find all choices at the frontier
        cur = netlist.execute("SELECT a, b, y FROM ands WHERE y IN ({})".format(",".join("?" * len(cone))), tuple(cone))
        and_choices = cur.fetchall()
        cur = netlist.execute("SELECT a, y FROM invs WHERE y IN ({})".format(",".join("?" * len(cone))), tuple(cone))
        inv_choices = cur.fetchall()
        # choose one with the smallest fanout
        best_choice, best_fanout = None, float("inf")
        for a, b, y in and_choices:
            fanout = netlist.fanout_of(a) + netlist.fanout_of(b)
            if fanout < best_fanout:
                best_choice = (a, b, y)
                best_fanout = fanout
        for a, y in inv_choices:
            fanout = netlist.fanout_of(a) * 2  # weight inverter more
            if fanout < best_fanout:
                best_choice = (a, y)
                best_fanout = fanout
        if best_choice is None:
            break
        if len(best_choice) == 3:   # choose an AND cell
            if len(cone) + 1 > k:   # cannot add both inputs
                break
            a, b, y = best_choice
            cone.remove(y)
            cone.add(a)
            cone.add(b)
        else:   # choose an inverter
            a, y = best_choice
            cone.remove(y)
            cone.add(a)
    return cone

def techmap_luts(netlist: NetlistDB, k: int, cnt: int, rseed: int):
    """
    Techmap the netlist with cnt k-LUTs
    """
    if netlist.VERBOSE:
        print(f"Techmapping to {k}-LUTs with random seed {rseed}")

    # count the shared times of each wire
    shared_wires: dict[int, int] = {}
    cur = netlist.execute("SELECT a, b FROM ands")
    for a, b in cur.fetchall():
        if a not in shared_wires:
            shared_wires[a] = 0
        if b not in shared_wires:
            shared_wires[b] = 0
        shared_wires[a] += 1
        shared_wires[b] += 1
    cur = netlist.execute("SELECT a FROM invs")
    for (a,) in cur.fetchall():
        if a not in shared_wires:
            shared_wires[a] = 0
        shared_wires[a] += 1

    # choose cnt wires randomly, with probability proportional to shared times
    cur = netlist.execute("SELECT source FROM from_inputs")
    inputs = {row[0] for row in cur.fetchall()}
    # ignore constant 0/1 and primary inputs
    shared_wires = {w: cnt for w, cnt in shared_wires.items() if w not in inputs and w not in {0, 1}}
    wires = list(shared_wires.keys())
    weights = [shared_wires[w] for w in wires]
    random.seed(rseed)
    chosen_wires = random.choices(wires, weights=weights, k=cnt)
    for w in chosen_wires:
        if netlist.VERBOSE:
            print(f"Chosen wire {w} with shared times {shared_wires[w]}")
        cone = find_cone(netlist, k, w)
        if netlist.VERBOSE:
            print(f"  Cone: {cone}")
        ins = netlist._create_or_lookup_wireset(cone)
        netlist.execute("INSERT OR IGNORE INTO luts (ins, out) VALUES (?, ?)", (ins, w))
        netlist.commit()
