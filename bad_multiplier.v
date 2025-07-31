module top (
    input clk,
    input [3:0] a,
    input [3:0] b,
    output [7:0] out
);
    // pipeline depth = 2
    // need to retime the multiplication
    reg [3:0] out_reg0, out_reg1;

    always @(posedge clk) begin
        out_reg0 <= a;
        out_reg1 <= b;
    end

    assign out = out_reg0 * out_reg1;
endmodule