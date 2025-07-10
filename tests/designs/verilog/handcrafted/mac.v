module mac (
    input clk,
    input [15:0] a,
    input [15:0] b,
    input [31:0] c,
    output [31:0] out
);
    // This module needs retiming and comm
    reg [15:0] a_reg, b_reg;
    reg [31:0] c_reg;

    always @(posedge clk) begin
        a_reg <= a;
        b_reg <= b;
        c_reg <= c;
    end

    assign out = c_reg + a_reg * b_reg;

endmodule