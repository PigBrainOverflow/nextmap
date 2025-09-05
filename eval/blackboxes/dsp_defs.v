module signed_mul_1_stage_26_17_48_bit (
    input clk,
    input signed [25:0] a,
    input signed [16:0] b,
    output signed [47:0] p
);
    // no implementation
endmodule

module signed_muladd_1_stage_26_17_48_bit (
    input clk,
    input signed [25:0] a,
    input signed [16:0] b,
    input signed [47:0] c,
    output signed [47:0] p
);
    // no implementation
endmodule

module unsigned_muladd_1_stage_27_18_48_bit (
    input clk,
    input [26:0] a,
    input [17:0] b,
    input [47:0] c,
    output [47:0] p
);
    // no implementation
endmodule

module signed_mulsub_1_stage_27_18_48_bit (
    input clk,
    input signed [26:0] a,
    input signed [17:0] b,
    input signed [47:0] c,
    output signed [47:0] p
);
    // no implementation
endmodule

module signed_submuladd_1_stage_26_18_48_26_bit (
    input clk,
    input signed [25:0] d,
    input signed [25:0] a,
    input signed [17:0] b,
    input signed [47:0] c,
    output signed [47:0] p
);
    // no implementation
endmodule

module signed_addmuladd_1_stage_26_18_48_26_bit (
    input clk,
    input signed [25:0] a,
    input signed [25:0] d,
    input signed [17:0] b,
    input signed [47:0] c,
    output signed [47:0] p
);
    // no implementation
endmodule

module signed_submul_1_stage_27_18_48_bit (
    input clk,
    input signed [26:0] d,
    input signed [26:0] a,
    input signed [17:0] b,
    output signed [47:0] p
);
    // no implementation
endmodule

module signed_mul_2_stage_26_17_48_bit_rst (
    input clk,
    input signed [25:0] a,
    input signed [16:0] b,
    input rst,
    output signed [47:0] p
);
    // no implementation
endmodule

module signed_square_diff_1_stage_18_bit (
    input clk,
    input signed [17:0] a,
    input signed [17:0] d,
    output signed [35:0] p
);
    // no implementation
endmodule

module signed_muladd_1_stage_27_18_48_bit_with_ab_out (
    input clk,
    input signed [26:0] a,
    input signed [17:0] b,
    input signed [47:0] c,
    output signed [26:0] a_out,
    output signed [17:0] b_out,
    output signed [47:0] p
);
    // no implementation
endmodule