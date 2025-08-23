module top (
    input clk,
    input [15:0] a, b,
    input [31:0] c,
    output [31:0] p
);
    // pipeline depth = 2
    reg [31:0] p_reg0, p_reg1;

    always @(posedge clk) begin
        p_reg0 <= (a * b) + c;
        p_reg1 <= p_reg0;
    end

    assign p = p_reg1;
endmodule