import prim_gen as pg


if __name__ == "__main__":
    prims = []

    ########################################
    # 1-stage 26-17-48-bit unsigned muladd #
    ########################################
    a = pg.BasicDialect.InputOp("a", 26)
    b = pg.BasicDialect.InputOp("b", 17)
    c = pg.BasicDialect.InputOp("c", 48)
    clk = pg.BasicDialect.InputOp("clk", 1)

    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.DelayOp(clk,
        ((a * b)[0:42] + c)[0:47]
    ))

    prims.append((
        "unsigned_muladd_1_stage_26_17_48_bit",
        [out],
        [a, b, c],
        1,
        "clk"  # clock for 1-stage
    ))


    ########################################
    # 1-stage 26-17-48-bit unsigned mulsub #
    ########################################
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.DelayOp(clk,
        ((a * b)[0:42] - c)[0:47]
    ))

    prims.append((
        "unsigned_mulsub_1_stage_26_17_48_bit",
        [out],
        [a, b, c],
        1,
        "clk"  # clock for 1-stage
    ))


    ##############################################
    # 1-stage 25-17-48-25-bit unsigned addmuladd #
    ##############################################
    a = pg.BasicDialect.InputOp("a", 25)
    d = pg.BasicDialect.InputOp("d", 25)

    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.DelayOp(clk,
        (((a + d)[0:25] * b)[0:42] + c[0:47])[0:47]
    ))

    prims.append((
        "unsigned_addmuladd_1_stage_25_17_48_25_bit",
        [out],
        [a, b, c, d],
        1,
        "clk"  # clock for 1-stage
    ))


    ##############################################
    # 1-stage 25-17-48-25-bit unsigned addmulsub #
    ##############################################
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.DelayOp(clk,
        (((a + d)[0:25] * b)[0:42] - c[0:47])[0:47]
    ))

    prims.append((
        "unsigned_addmulsub_1_stage_25_17_48_25_bit",
        [out],
        [a, b, c, d],
        1,
        "clk"  # clock for 1-stage
    ))


    # failure
    ##############################################
    # 1-stage 25-17-48-25-bit unsigned submuladd #
    ##############################################
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.DelayOp(clk,
        (((a - d)[0:25] * b)[0:42] + c[0:47])[0:47]
    ))

    prims.append((
        "unsigned_submuladd_1_stage_25_17_48_25_bit",
        [out],
        [a, b, c, d],
        1,
        "clk"  # clock for 1-stage
    ))


    # failure
    ##############################################
    # 1-stage 25-17-48-25-bit unsigned submulsub #
    ##############################################
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.DelayOp(clk,
        (((a - d)[0:25] * b)[0:42] - c[0:47])[0:47]
    ))

    prims.append((
        "unsigned_submulsub_1_stage_25_17_48_25_bit",
        [out],
        [a, b, c, d],
        1,
        "clk"  # clock for 1-stage
    ))


    # 3-stage signed squarediff
    a = pg.BasicDialect.InputOp("a", 16)
    d = pg.BasicDialect.InputOp("d", 16)
    diff = (d - a)[0:16]


    # generate all primitives
    impls = pg.generate_all_prims(
        arch_name="xilinx-ultrascale-plus",
        tech_name="dsp48e2",
        template="dsp",
        prims=[prims[-1]],
        lakeroad_path="./lakeroad/bin",
        verbose=True
    )

    with open("dsp48e2_behavioral_usages.v", "w") as f1, open("dsp48e2_structural_usages.v", "w") as f2:
        for behavioral, structural in impls:
            if structural is not None:
                f1.write(behavioral + "\n\n")
                f2.write(structural + "\n\n")
            else:
                f1.write("/*\n" + behavioral + "\n*/\n\n")  # comment out if generation failed