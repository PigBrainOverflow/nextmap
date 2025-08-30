import pyrtl


if __name__ == "__main__":
    mem = pyrtl.MemBlock(bitwidth=8, addrwidth=4, max_read_ports=1, max_write_ports=1, asynchronous=True)
    raddr = pyrtl.Input(4, "raddr")
    rdata = pyrtl.Output(8, "rdata")
    waddr = pyrtl.Input(4, "waddr")
    wdata = pyrtl.Input(8, "wdata")
    we = pyrtl.Input(1, "we")

    rdata <<= mem[raddr]
    mem[waddr] <<= pyrtl.MemBlock.EnabledWrite(wdata, we)

    sim = pyrtl.Simulation()
    for cycle in range(16):
        sim.step({
            "raddr": cycle - 1 if cycle > 0 else 0,
            "waddr": cycle,
            "wdata": 1,
            "we": 1
        })
        print(f"Cycle {cycle}: {sim.inspect_mem(mem)} | rdata: {sim.inspect('rdata')}")