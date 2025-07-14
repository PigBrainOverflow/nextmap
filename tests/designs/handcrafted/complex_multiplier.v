module top (
    input clk,
    input signed [15:0] ar, ai,
    input signed [15:0] br, bi,
    output signed [31:0] pr, pi
);
    // pipeline depth = 2
    wire signed [31:0] pr_tmp, pi_tmp;
    assign pr_tmp = (ar * br) - (ai * bi);
    assign pi_tmp = (ar * bi) + (ai * br);

    reg signed [31:0] pr_reg0, pi_reg0, pr_reg1, pi_reg1;

    always @(posedge clk) begin
        pr_reg0 <= pr_tmp;
        pi_reg0 <= pi_tmp;
        pr_reg1 <= pr_reg0;
        pi_reg1 <= pi_reg0;
    end

    assign pr = pr_reg1;
    assign pi = pi_reg1;
endmodule