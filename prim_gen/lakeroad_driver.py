import subprocess
from .ir import *


def generate_all_prims(
    tech_name: str,
    prims: list[
        tuple[
            str,                            # primitive name
            list[BasicDialect.OutputOp],    # outputs
            list[BasicDialect.InputOp],     # inputs
            int,                            # pipeline depth
            str | None                      # clock name
        ]
    ],
    tmp_dir: str = ".",
    timeout: int = 90,
    verbose: bool = False
) -> list[str | None]:
    # returns a list of verilog code for each primitive, or None if generation failed

    print(f"Generating primitives for {tech_name}...")
    print(f"Total primitives to synthesize: {len(prims)}")

    impls = []
    builder = BehavioralVerilogBuilder()
    for i, (name, outputs, inputs, depth, clk) in enumerate(prims):
        if verbose:
            print(f"  [{i+1}/{len(prims)}] Generating primitive {name}...")

        # add inputs
        for inp in inputs:
            inp.build(builder)

        # add outputs
        for out in outputs:
            out.build(builder)

        # add clock if needed
        if clk is not None:
            clk_op = BasicDialect.InputOp(clk, 1)
            clk_op.build(builder)

        # add pipeline registers if needed
        if depth > 0 and clk is not None:
            for d in range(depth):
                for out in outputs:
                    reg_out = BasicDialect.OutputOp(f"{out.name}_reg{d}", out.input)
                    reg_inp = BasicDialect.InputOp(f"{out.name}_reg{d}", out.input)
                    reg = pg.FFRegOp(reg_out, reg_inp, clk_op)
                    reg.build(builder)
                    # connect previous stage to this register
                    if d == 0:
                        connect_op = BasicDialect.ConnectOp(out.input, reg_inp)
                    else:
                        connect_op = BasicDialect.ConnectOp(f"{out.name}_reg{d-1}", reg_inp)
                    connect_op.build(builder)
                # update output to be the register output for next stage
                for out in outputs:
                    out.input = f"{out.name}_reg{d}"

        verilog_code = builder.emit_verilog(name)

        # write to temp file
        with open("temp_prim.v", "w") as f:
            f.write(verilog_code)

        # run synthesis tool (e.g., Yosys) to check if it can be synthesized
        try:
            result = subprocess.run(
                ["yosys", "-p", f"synth_{tech_name}; write_verilog temp_out.v", "temp_prim.v"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode != 0:
                print("Failed (synthesis error)")
                impls.append(None)
                continue

            with open("temp_out.v", "r") as f:
                synthesized_code = f.read()
            impls.append(synthesized_code)
            print("Success")
        except subprocess.TimeoutExpired:
            print("Failed (timeout)")
            impls.append(None)

    return []