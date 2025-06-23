module two_stage_multiplier_dsp(a, b, clk, out);
  wire [47:0] P_0;
  input [15:0] a;
  wire [15:0] a;
  input [15:0] b;
  wire [15:0] b;
  input clk;
  wire clk;
  output [31:0] out;
  wire [31:0] out;
  DSP48E2 #(
    .ACASCREG(32'd0),
    .ADREG(32'd0),
    .ALUMODEREG(32'd0),
    .AMULTSEL("A"),
    .AREG(32'd0),
    .AUTORESET_PATDET("NO_RESET"),
    .AUTORESET_PRIORITY("RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(32'd0),
    .BMULTSEL("B"),
    .BREG(32'd0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(32'd0),
    .CARRYINSELREG(32'd0),
    .CREG(32'd0),
    .DREG(32'd0),
    .INMODEREG(32'd0),
    .IS_ALUMODE_INVERTED(4'h0),
    .IS_CARRYIN_INVERTED(1'h0),
    .IS_CLK_INVERTED(1'h0),
    .IS_INMODE_INVERTED(5'h00),
    .IS_OPMODE_INVERTED(9'h000),
    .IS_RSTALLCARRYIN_INVERTED(1'h0),
    .IS_RSTALUMODE_INVERTED(1'h0),
    .IS_RSTA_INVERTED(1'h0),
    .IS_RSTB_INVERTED(1'h0),
    .IS_RSTCTRL_INVERTED(1'h0),
    .IS_RSTC_INVERTED(1'h0),
    .IS_RSTD_INVERTED(1'h0),
    .IS_RSTINMODE_INVERTED(1'h0),
    .IS_RSTM_INVERTED(1'h0),
    .IS_RSTP_INVERTED(1'h0),
    .MASK(48'h000000000000),
    .MREG(32'd0),
    .OPMODEREG(32'd0),
    .PATTERN(48'h000000000000),
    .PREADDINSEL("A"),
    .PREG(32'd0),
    .RND(48'h000000000000),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48"),
    .USE_WIDEXOR("FALSE"),
    .XORSIMD("XOR12")
  ) DSP48E2_0 (
    .A({ 14'h0000, a }),
    .ACIN(30'h00000000),
    .ALUMODE(4'h1),
    .B({ 2'h0, b }),
    .BCIN(18'h00000),
    .C(48'h000000000000),
    .CARRYCASCIN(1'h0),
    .CARRYIN(1'h0),
    .CARRYINSEL(3'h1),
    .CEA1(1'h1),
    .CEA2(1'h1),
    .CEAD(1'h1),
    .CEALUMODE(1'h1),
    .CEB1(1'h1),
    .CEB2(1'h1),
    .CEC(1'h1),
    .CECARRYIN(1'h1),
    .CECTRL(1'h1),
    .CED(1'h1),
    .CEINMODE(1'h1),
    .CEM(1'h1),
    .CEP(1'h1),
    .CLK(clk),
    .D(27'h0000000),
    .INMODE(5'h0c),
    .MULTSIGNIN(1'h0),
    .OPMODE(9'h095),
    .P({ P_0[47:32], out }),
    .PCIN(48'h000000000000),
    .RSTA(1'h0),
    .RSTALLCARRYIN(1'h0),
    .RSTALUMODE(1'h0),
    .RSTB(1'h0),
    .RSTC(1'h0),
    .RSTCTRL(1'h0),
    .RSTD(1'h0),
    .RSTINMODE(1'h0),
    .RSTM(1'h0),
    .RSTP(1'h0)
  );
  assign P_0[31] = out[31];
  assign P_0[30] = out[30];
  assign P_0[29] = out[29];
  assign P_0[28] = out[28];
  assign P_0[27] = out[27];
  assign P_0[26] = out[26];
  assign P_0[25] = out[25];
  assign P_0[24] = out[24];
  assign P_0[23] = out[23];
  assign P_0[22] = out[22];
  assign P_0[21] = out[21];
  assign P_0[20] = out[20];
  assign P_0[19] = out[19];
  assign P_0[18] = out[18];
  assign P_0[17] = out[17];
  assign P_0[16] = out[16];
  assign P_0[15] = out[15];
  assign P_0[14] = out[14];
  assign P_0[13] = out[13];
  assign P_0[12] = out[12];
  assign P_0[11] = out[11];
  assign P_0[10] = out[10];
  assign P_0[9] = out[9];
  assign P_0[8] = out[8];
  assign P_0[7] = out[7];
  assign P_0[6] = out[6];
  assign P_0[5] = out[5];
  assign P_0[4] = out[4];
  assign P_0[3] = out[3];
  assign P_0[2] = out[2];
  assign P_0[1] = out[1];
  assign P_0[0] = out[0];
endmodule