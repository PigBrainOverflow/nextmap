module top (
    input wire clk,
    input signed [15:0] a,
    input signed [15:0] b,
    input signed [31:0] c,
    output signed [31:0] y
);
    reg signed [31:0] y_reg0, y_reg1, y_reg2;
    always @(posedge clk) begin
        y_reg0 <= a * b + c;
        y_reg1 <= y_reg0;
        y_reg2 <= y_reg1;
    end
    assign y = y_reg2;
endmodule