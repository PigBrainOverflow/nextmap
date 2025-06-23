/* Generated Module */
module two_stage_multiplier (
    input clk,
    input [15:0] a,
    input [15:0] b,
    output [31:0] out
);

    // declarations
    wire [31:0] wire_0;
    wire [31:0] wire_1;
    reg [31:0] reg_0;
    assign wire_0 = a * b;
    assign wire_1 = reg_0;
    assign out = wire_1;

    always @ (posedge clk) begin
        reg_0 <= wire_0;
    end

endmodule
