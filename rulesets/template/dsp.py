import prim_gen as pg


if __name__ == "__main__":
    builder = pg.BehavioralVerilogBuilder()

    # 1-stage 48-bit adder
    a = pg.BasicDialect.InputOp("a", 48)
    b = pg.BasicDialect.InputOp("b", 48)
    a_add_b = pg.BasicDialect.ExtractOp(pg.ArithDialect.AddOp(a, b), 47, 0)
    out = pg.BasicDialect.OutputOp("out", a_add_b)

    out.build(builder)
    builder.emit("")