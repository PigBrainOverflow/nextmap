// Squarer support for DSP block (DSP48E2) with
// pre-adder configured
// as subtractor
// File: squarediffmult.v

module squarediffmult # (parameter SIZEIN = 16)
(
    input clk,
    input signed [SIZEIN-1:0] a, b,
    output signed [2*SIZEIN+1:0] square_out
);

// Declare registers for intermediate values
reg signed [SIZEIN-1:0] a_reg, b_reg;
reg signed [SIZEIN:0] diff_reg;
reg signed [2*SIZEIN+1:0] m_reg;

always @(posedge clk) begin
    a_reg <= a;
    b_reg <= b;
    diff_reg <= a_reg - b_reg;
    m_reg <= diff_reg * diff_reg;
end

// Output result
assign square_out = m_reg;

endmodule // squarediffmult
