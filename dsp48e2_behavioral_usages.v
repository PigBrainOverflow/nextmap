// Generated Module
module unsigned_muladd_1_stage_26_17_48_bit (
    input clk,
    input [25:0] a,
    input [16:0] b,
    input [47:0] c,
    output [47:0] out
);

    // declarations
    wire [42:0] wire_0;
    wire [47:0] wire_1;
    wire [47:0] wire_3;
    reg [47:0] reg_2;
    assign wire_0 = a * b;
    assign wire_1 = wire_0 + c;
    assign wire_3 = reg_2;
    assign out = wire_3;

    always @ (posedge clk) begin
        reg_2 <= wire_1;
    end

endmodule


// Generated Module
module unsigned_mulsub_1_stage_26_17_48_bit (
    input clk,
    input [25:0] a,
    input [16:0] b,
    input [47:0] c,
    output [47:0] out
);

    // declarations
    wire [42:0] wire_0;
    wire [47:0] wire_1;
    wire [47:0] wire_3;
    reg [47:0] reg_2;
    assign wire_0 = a * b;
    assign wire_1 = wire_0 - c;
    assign wire_3 = reg_2;
    assign out = wire_3;

    always @ (posedge clk) begin
        reg_2 <= wire_1;
    end

endmodule


// Generated Module
module unsigned_addmuladd_1_stage_25_17_48_25_bit (
    input clk,
    input [24:0] a,
    input [24:0] d,
    input [16:0] b,
    input [47:0] c,
    output [47:0] out
);

    // declarations
    wire [25:0] wire_0;
    wire [42:0] wire_1;
    wire [47:0] wire_2;
    wire [47:0] wire_3;
    wire [47:0] wire_5;
    reg [47:0] reg_4;
    assign wire_0 = a + d;
    assign wire_1 = wire_0 * b;
    assign wire_2 = c[47:0];
    assign wire_3 = wire_1 + wire_2;
    assign wire_5 = reg_4;
    assign out = wire_5;

    always @ (posedge clk) begin
        reg_4 <= wire_3;
    end

endmodule


// Generated Module
module unsigned_addmulsub_1_stage_25_17_48_25_bit (
    input clk,
    input [24:0] a,
    input [24:0] d,
    input [16:0] b,
    input [47:0] c,
    output [47:0] out
);

    // declarations
    wire [25:0] wire_0;
    wire [42:0] wire_1;
    wire [47:0] wire_2;
    wire [47:0] wire_3;
    wire [47:0] wire_5;
    reg [47:0] reg_4;
    assign wire_0 = a + d;
    assign wire_1 = wire_0 * b;
    assign wire_2 = c[47:0];
    assign wire_3 = wire_1 - wire_2;
    assign wire_5 = reg_4;
    assign out = wire_5;

    always @ (posedge clk) begin
        reg_4 <= wire_3;
    end

endmodule


/*
// Generated Module
module unsigned_submuladd_1_stage_25_17_48_25_bit (
    input clk,
    input [24:0] a,
    input [24:0] d,
    input [16:0] b,
    input [47:0] c,
    output [47:0] out
);

    // declarations
    wire [25:0] wire_0;
    wire [42:0] wire_1;
    wire [47:0] wire_2;
    wire [47:0] wire_3;
    wire [47:0] wire_5;
    reg [47:0] reg_4;
    assign wire_0 = a - d;
    assign wire_1 = wire_0 * b;
    assign wire_2 = c[47:0];
    assign wire_3 = wire_1 + wire_2;
    assign wire_5 = reg_4;
    assign out = wire_5;

    always @ (posedge clk) begin
        reg_4 <= wire_3;
    end

endmodule

*/

/*
// Generated Module
module unsigned_submulsub_1_stage_25_17_48_25_bit (
    input clk,
    input [24:0] a,
    input [24:0] d,
    input [16:0] b,
    input [47:0] c,
    output [47:0] out
);

    // declarations
    wire [25:0] wire_0;
    wire [42:0] wire_1;
    wire [47:0] wire_2;
    wire [47:0] wire_3;
    wire [47:0] wire_5;
    reg [47:0] reg_4;
    assign wire_0 = a - d;
    assign wire_1 = wire_0 * b;
    assign wire_2 = c[47:0];
    assign wire_3 = wire_1 - wire_2;
    assign wire_5 = reg_4;
    assign out = wire_5;

    always @ (posedge clk) begin
        reg_4 <= wire_3;
    end

endmodule

*/

// Generated Module
module signed_mul_1_stage_27_18_bit (
    input clk,
    input [26:0] a,
    input [17:0] b,
    output [44:0] out
);

    // declarations
    wire signed [26:0] wire_0;
    wire signed [17:0] wire_1;
    wire [44:0] wire_2;
    wire [44:0] wire_4;
    reg [44:0] reg_3;
    assign wire_0 = a;
    assign wire_1 = b;
    assign wire_2 = wire_0 * wire_1;
    assign wire_4 = reg_3;
    assign out = wire_4;

    always @ (posedge clk) begin
        reg_3 <= wire_2;
    end

endmodule


// Generated Module
module signed_squarediff_3_stage_17_bit (
    input clk,
    input [16:0] d,
    input [16:0] a,
    output [35:0] out
);

    // declarations
    wire [17:0] wire_0;
    wire signed [17:0] wire_1;
    wire [35:0] wire_2;
    wire [35:0] wire_4;
    wire [35:0] wire_6;
    wire [35:0] wire_8;
    reg [35:0] reg_3;
    reg [35:0] reg_5;
    reg [35:0] reg_7;
    assign wire_0 = d - a;
    assign wire_1 = wire_0;
    assign wire_2 = wire_1 * wire_1;
    assign wire_4 = reg_3;
    assign wire_6 = reg_5;
    assign wire_8 = reg_7;
    assign out = wire_8;

    always @ (posedge clk) begin
        reg_3 <= wire_2;
        reg_5 <= wire_4;
        reg_7 <= wire_6;
    end

endmodule


