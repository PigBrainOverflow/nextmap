module top (
    input wire clk,
    input signed [15:0] a,
    input signed [15:0] b,
    input signed [31:0] c,
    output signed [31:0] y
);
    reg signed [31:0] y_reg;
    always @(posedge clk) begin
        y_reg <= a * b + c;
    end
    assign y = y_reg;
endmodule