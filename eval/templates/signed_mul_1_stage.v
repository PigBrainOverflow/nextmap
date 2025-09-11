module top (
    input clk,
    input signed [15:0] a,
    input signed [15:0] b,
    output signed [31:0] y
);
    reg signed [31:0] y_reg;
    always @(posedge clk) begin
        y_reg <= a * b;
    end
    assign y = y_reg;
endmodule