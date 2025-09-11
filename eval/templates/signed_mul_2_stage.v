module top (
    input clk,
    input signed [15:0] a,
    input signed [15:0] b,
    output signed [31:0] y
);
    reg signed [31:0] y_reg0, y_reg1;
    always @(posedge clk) begin
        y_reg0 <= a * b;
        y_reg1 <= y_reg0;
    end
    assign y = y_reg1;
endmodule