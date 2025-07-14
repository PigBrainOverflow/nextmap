module top (
    input clk,
    input signed [15:0] a, b,
    output signed [33:0] square_out
);
    // pipeline depth = 3
    reg signed [15:0] a_reg, b_reg;
    reg signed [16:0] diff_reg;
    reg signed [33:0] m_reg;

    always @(posedge clk) begin
        a_reg <= a;
        b_reg <= b;
        diff_reg <= a_reg - b_reg;
        m_reg <= diff_reg * diff_reg;
    end

    assign square_out = m_reg;
endmodule