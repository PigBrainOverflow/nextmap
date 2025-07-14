\ Model egraph_extraction
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  256 y[1] + 256 y[2] + 64 y[4] + 64 y[5] + 16 z[0] + 16 z[1] + 16 z[2]
   + 16 z[3]
Subject To
 output_group5_constraint: x[5] >= 1
 wire_group0_constraint: - x[0] + y[4] >= 0
 wire_group1_constraint: - x[1] + y[2] >= 0
 wire_group2_constraint: - x[2] + y[5] + z[0] >= 0
 wire_group4_constraint: - x[4] + y[1] >= 0
 wire_group5_constraint: - x[5] + z[1] >= 0
 wire_group6_constraint: - x[6] + y[0] + z[3] >= 0
 wire_group7_constraint: - x[7] + y[3] + z[2] >= 0
 cell_0_input_group9_constraint: x[9] - y[0] >= 0
 cell_0_input_group8_constraint: x[8] - y[0] >= 0
 cell_1_input_group8_constraint: x[8] - y[1] >= 0
 cell_2_input_group3_constraint: x[3] - y[2] >= 0
 cell_3_input_group3_constraint: x[3] - y[3] >= 0
 cell_3_input_group9_constraint: x[9] - y[3] >= 0
 cell_4_input_group4_constraint: x[4] - y[4] >= 0
 cell_4_input_group1_constraint: x[1] - y[4] >= 0
 cell_5_input_group7_constraint: x[7] - y[5] >= 0
 cell_5_input_group6_constraint: x[6] - y[5] >= 0
 dff_0_input_group0_constraint: x[0] - z[0] >= 0
 dff_0_clk_group9_constraint: x[9] - z[0] >= 0
 dff_1_input_group2_constraint: x[2] - z[1] >= 0
 dff_1_clk_group9_constraint: x[9] - z[1] >= 0
 dff_2_input_group1_constraint: x[1] - z[2] >= 0
 dff_2_clk_group9_constraint: x[9] - z[2] >= 0
 dff_3_input_group4_constraint: x[4] - z[3] >= 0
 dff_3_clk_group9_constraint: x[9] - z[3] >= 0
 dsp_count_constraint: y[0] + y[3] <= 3
Bounds
Binaries
 x[0] x[1] x[2] x[3] x[4] x[5] x[6] x[7] x[8] x[9] y[0] y[1] y[2] y[3] y[4]
 y[5] z[0] z[1] z[2] z[3]
End
