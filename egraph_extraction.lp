\ Model egraph_extraction
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  0 x[0] + 2 y[0] + 2 y[1] + 2 y[2] + 2 y[3]
Subject To
 output_group6_constraint: x[6] >= 1
 output_group3_constraint: x[3] >= 1
 output_group1_constraint: x[1] >= 1
 wire_group2_constraint: - x[2] + y[0] >= 0
 wire_group3_constraint: - x[3] + y[3] >= 0
 wire_group6_constraint: - x[6] + y[2] >= 0
 wire_group7_constraint: - x[7] + y[1] >= 0
 cell_0_input_group5_constraint: x[5] - y[0] >= 0
 cell_1_input_group6_constraint: x[6] - y[1] >= 0
 cell_1_input_group9_constraint: x[9] - y[1] >= 0
 cell_2_input_group2_constraint: x[2] - y[2] >= 0
 cell_2_input_group4_constraint: x[4] - y[2] >= 0
 cell_3_input_group8_constraint: x[8] - y[3] >= 0
 cell_3_input_group7_constraint: x[7] - y[3] >= 0
 dsp_count_constraint: <= 3
Bounds
Binaries
 x[0] x[1] x[2] x[3] x[4] x[5] x[6] x[7] x[8] x[9] y[0] y[1] y[2] y[3]
End
