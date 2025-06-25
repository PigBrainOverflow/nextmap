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

    a_mul_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.MulOp(a, b), 42, 0)
    a_mul_b_add_c = pg.BasicDialect.ExtractOp(pg.ArithDialect.AddOp(a_mul_b, c), 47, 0)
    a_mul_b_add_c_delay_1 = pg.BasicDialect.DelayOp(clk, a_mul_b_add_c)
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.ExtractOp(a_mul_b_add_c_delay_1, 47, 0))

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
    a = pg.BasicDialect.InputOp("a", 26)
    b = pg.BasicDialect.InputOp("b", 17)
    c = pg.BasicDialect.InputOp("c", 48)
    clk = pg.BasicDialect.InputOp("clk", 1)

    a_mul_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.MulOp(a, b), 42, 0)
    a_mul_b_sub_c = pg.BasicDialect.ExtractOp(pg.ArithDialect.SubOp(a_mul_b, c), 47, 0)
    a_mul_b_sub_c_delay_1 = pg.BasicDialect.DelayOp(clk, a_mul_b_sub_c)
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.ExtractOp(a_mul_b_sub_c_delay_1, 47, 0))

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

    a_add_d = pg.BasicDialect.ExtractOp(pg.ArithDialect.AddOp(a, d), 25, 0)
    a_add_d_mul_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.MulOp(a_add_d, b), 42, 0)
    a_add_d_mul_b_add_c = pg.BasicDialect.ExtractOp(pg.ArithDialect.AddOp(a_add_d_mul_b, c), 47, 0)
    a_add_d_mul_b_add_c_delay_1 = pg.BasicDialect.DelayOp(clk, a_add_d_mul_b_add_c)
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.ExtractOp(a_add_d_mul_b_add_c_delay_1, 47, 0))

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
    a_add_d = pg.BasicDialect.ExtractOp(pg.ArithDialect.AddOp(a, d), 25, 0)
    a_add_d_mul_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.MulOp(a_add_d, b), 42, 0)
    a_add_d_mul_b_sub_c = pg.BasicDialect.ExtractOp(pg.ArithDialect.SubOp(a_add_d_mul_b, c), 47, 0)
    a_add_d_mul_b_sub_c_delay_1 = pg.BasicDialect.DelayOp(clk, a_add_d_mul_b_sub_c)
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.ExtractOp(a_add_d_mul_b_sub_c_delay_1, 47, 0))

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
    a_sub_d = pg.BasicDialect.ExtractOp(pg.ArithDialect.SubOp(a, d), 25, 0)
    a_sub_d_mul_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.MulOp(a_sub_d, b), 42, 0)
    a_sub_d_mul_b_add_c = pg.BasicDialect.ExtractOp(pg.ArithDialect.AddOp(a_sub_d_mul_b, c), 47, 0)
    a_sub_d_mul_b_add_c_delay_1 = pg.BasicDialect.DelayOp(clk, a_sub_d_mul_b_add_c)
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.ExtractOp(a_sub_d_mul_b_add_c_delay_1, 47, 0))

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
    a_sub_d = pg.BasicDialect.ExtractOp(pg.ArithDialect.SubOp(a, d), 25, 0)
    a_sub_d_mul_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.MulOp(a_sub_d, b), 42, 0)
    a_sub_d_mul_b_sub_c = pg.BasicDialect.ExtractOp(pg.ArithDialect.SubOp(a_sub_d_mul_b, c), 47, 0)
    a_sub_d_mul_b_sub_c_delay_1 = pg.BasicDialect.DelayOp(clk, a_sub_d_mul_b_sub_c)
    out = pg.BasicDialect.OutputOp("out", pg.BasicDialect.ExtractOp(a_sub_d_mul_b_sub_c_delay_1, 47, 0))

    prims.append((
        "unsigned_submulsub_1_stage_25_17_48_25_bit",
        [out],
        [a, b, c, d],
        1,
        "clk"  # clock for 1-stage
    ))


    # generate all primitives
    impls = pg.generate_all_prims(
        arch_name="xilinx-ultrascale-plus",
        tech_name="dsp48e2",
        template="dsp",
        prims=prims,
        lakeroad_path="./lakeroad/bin",
        verbose=True
    )

    with open("dsp48e2_usages.v", "w") as f:
        for impl in impls:
            if impl is not None:
                f.write(impl + "\n\n")
