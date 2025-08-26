module multiplier_with_rst (
    input clk,
    input rst,
    input [15:0] a,
    input [15:0] b,
    output [31:0] p
);
    // synchronous reset
    reg [15:0] a_reg, b_reg;
    reg [31:0] p_reg;
    always @(posedge clk) begin
        if (rst) begin
            a_reg <= 16'b0;
            b_reg <= 16'b0;
            p_reg <= 32'b0;
        end
        else begin
            a_reg <= a;
            b_reg <= b;
            p_reg <= a_reg * b_reg;
        end
    end

    assign p = p_reg;
endmodule