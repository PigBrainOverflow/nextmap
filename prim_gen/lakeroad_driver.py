import subprocess
from .ir import *


def generate_all_prims(
    arch_name: str,
    tech_name: str,
    template: str,
    prims: list[
        tuple[
            str,                            # primitive name
            list[BasicDialect.OutputOp],    # outputs
            list[BasicDialect.InputOp],     # inputs
            int,                            # pipeline depth
            str | None                      # clock name
        ]
    ],
    lakeroad_path: str = ".",
    tmp_dir: str = ".",
    timeout: int = 90,
    extra_cycles: int = 0,
    verbose: bool = False
) -> list[str | None]:
    # returns a list of verilog code for each primitive, or None if generation failed

    if verbose:
        print(f"Generating primitives for {tech_name}...")
        print(f"Total primitives to synthesize: {len(prims)}")

    impls = []
    builder = BehavioralVerilogBuilder()
    tmp_path = f"{tmp_dir}/tmp.v"

    for i, (name, outputs, inputs, depth, clk) in enumerate(prims):
        if verbose:
            print(f"  [{i+1}/{len(prims)}] Generating primitive {name}... ")

        builder.clear()

        # process config
        cmd = [
            f"{lakeroad_path}/lakeroad",
            "--verilog-module-filepath", tmp_path,
            "--top-module-name", name,
            "--architecture", arch_name,
            "--template", template,
            "--pipeline-depth", str(depth),
            "--bitwuzla", "--stp", "--yices", "--cvc5",
            "--timeout", str(timeout),
            "--extra-cycles", str(extra_cycles),
            "--out-format", "verilog",
            "--module-name", f"{name}_{tech_name}_impl"
        ]
        if clk is not None:
            cmd.append("--clock-name")
            cmd.append(clk)

        # process inputs
        for input in inputs:
            if clk and input.name == clk:
                continue
            cmd.append("--input-signal")
            cmd.append(f"{input.name}:(port {input.name} {input.width}):{input.width}")

        # process outputs
        if not outputs or len(outputs) > 1:
            print(f"Warning: Primitive {name} has no outputs or multiple outputs, skipping synthesis.")
            impls.append(None)
            continue
        output = outputs[0]
        output.build(builder)
        with open(tmp_path, "w") as f:
            f.write(builder.emit(name, clk))
        cmd.append("--verilog-module-out-signal")
        cmd.append(f"{output.name}:{output.width}")

        # print(" ".join(cmd))

        # run lakeroad
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                if verbose:
                    print("  Synthesis failed")
                impls.append(None)
            else:
                if verbose:
                    print("  Synthesis successful")
                with open(tmp_path, "r") as f:
                    impls.append(result.stdout.strip())
        except subprocess.TimeoutExpired:
            if verbose:
                print("  Synthesis timed out")
            impls.append(None)

    if verbose:
        print(f"{sum(impl is not None for impl in impls)} out of {len(prims)} primitives synthesized successfully.")

    return impls