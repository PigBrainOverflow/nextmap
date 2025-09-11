module top (
    input wire clk,
    input signed [15:0] a,
    input signed [15:0] d,
    input signed [15:0] b,
    input signed [31:0] c,
    input wire rst,
    output signed [31:0] y
);
    reg signed [15:0] a_reg, d_reg, b_reg;
    reg signed [31:0] y_reg;
    wire signed [16:0] ad_sum = a_reg + d_reg;
    always @(posedge clk) begin
        if (rst) begin
            a_reg <= 16'sd0;
            d_reg <= 16'sd0;
            b_reg <= 16'sd0;
        end else begin
            a_reg <= a;
            d_reg <= d;
            b_reg <= b;
        end
        y_reg <= ad_sum * b_reg - c;
    end
    assign y = y_reg;
endmodule