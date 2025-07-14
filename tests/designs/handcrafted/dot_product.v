module top (
    input clk,
    input signed [15:0] a0, a1,
    input signed [15:0] b0, b1,
    output signed [31:0] p
);
    // pipeline depth = 2
    reg signed [31:0] p_reg0, p_reg1;

    always @(posedge clk) begin
        p_reg0 <= (a0 * b0) + (a1 * b1);
        p_reg1 <= p_reg0;
    end

    assign p = p_reg1;
endmodule