module top (
    input clk,
    input [15:0] a,
    input [15:0] b,
    output [15:0] y
);
    // 16-bit truncated multiplier with pipeline depth 2
    reg [15:0] a_reg0, a_reg1, b_reg0, b_reg1;
    always @(posedge clk) begin
        a_reg0 <= a;
        b_reg0 <= b;
        a_reg1 <= a_reg0;
        b_reg1 <= b_reg0;
    end
    assign y = a_reg1 * b_reg1;
endmodule