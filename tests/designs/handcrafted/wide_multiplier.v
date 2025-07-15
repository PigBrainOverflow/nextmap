module top (
    input clk,
    input [15:0] a,
    input [31:0] b,
    output [31:0] out
);
    // pipeline depth = 2
    reg [31:0] out_reg0, out_reg1;

    always @(posedge clk) begin
        out_reg0 <= a * b;
        out_reg1 <= out_reg0;
    end

    assign out = out_reg1;
endmodule