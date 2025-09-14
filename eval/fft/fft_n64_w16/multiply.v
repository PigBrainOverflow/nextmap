//----------------------------------------------------------------------
//  Multiply: Complex Multiplier
//----------------------------------------------------------------------
module Multiply #(
    parameter   WIDTH = 16
)(
    input   signed  [WIDTH-1:0] a_re,
    input   signed  [WIDTH-1:0] a_im,
    input   signed  [WIDTH-1:0] b_re,
    input   signed  [WIDTH-1:0] b_im,
    output  signed  [WIDTH-1:0] m_re,
    output  signed  [WIDTH-1:0] m_im
);

wire signed [WIDTH*2-1:0]   arbr, arbi, aibr, aibi;
wire signed [WIDTH-1:0]     sc_arbr, sc_arbi, sc_aibr, sc_aibi;

//  Signed Multiplication
assign  arbr = a_re * b_re;
assign  arbi = a_re * b_im;
assign  aibr = a_im * b_re;
assign  aibi = a_im * b_im;

wire signed [WIDTH*2-1:0] unsc_m_re, unsc_m_im;
assign  unsc_m_re = arbr - aibi;
assign  unsc_m_im = arbi + aibr;

//  Scaling
assign  m_re = unsc_m_re[WIDTH*2-1:WIDTH];
assign  m_im = unsc_m_im[WIDTH*2-1:WIDTH];

endmodule