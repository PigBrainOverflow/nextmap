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

