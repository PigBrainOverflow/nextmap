module top (
    input clk,
    input rst,
    input signed [15:0] a,
    input signed [15:0] b,
    output signed [31:0] p
);
    // synchronous reset
    reg signed [15:0] a_reg, b_reg;
    reg signed [31:0] p_reg;
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