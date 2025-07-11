\ Model egraph_extraction
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  y[0] + y[1] + y[3] + 100 y[4] + 100 y[5] + y[6] + y[7] + y[8] + 100 y[9]
   + y[10] + y[11] + y[12] + 100 y[13] + y[14] + 100 y[16] + 100 y[17]
   + 100 y[18] + y[19] + z[0] + z[1] + z[2] + z[3] + z[4] + z[5] + z[6]
   + z[7] + z[8]
Subject To
 output_group19_constraint: x[19] >= 1
 output_group8_constraint: x[8] >= 1
 wire_group0_constraint: - x[0] + y[4] >= 0
 wire_group2_constraint: - x[2] + y[5] >= 0
 wire_group3_constraint: - x[3] + z[5] >= 0
 wire_group4_constraint: - x[4] + y[6] >= 0
 wire_group5_constraint: - x[5] + y[17] >= 0
 wire_group6_constraint: - x[6] + y[15] >= 0
 wire_group7_constraint: - x[7] + z[7] >= 0
 wire_group8_constraint: - x[8] + z[1] >= 0
 wire_group9_constraint: - x[9] + y[8] + y[14] + z[2] >= 0
 wire_group10_constraint: - x[10] + y[9] >= 0
 wire_group11_constraint: - x[11] + y[11] >= 0
 wire_group12_constraint: - x[12] + y[0] + y[10] >= 0
 wire_group14_constraint: - x[14] + y[2] >= 0
 wire_group15_constraint: - x[15] + y[16] >= 0
 wire_group16_constraint: - x[16] + y[13] >= 0
 wire_group17_constraint: - x[17] + z[4] >= 0
 wire_group18_constraint: - x[18] + y[18] >= 0
 wire_group19_constraint: - x[19] + z[0] >= 0
 wire_group20_constraint: - x[20] + z[8] >= 0
 wire_group21_constraint: - x[21] + y[3] + y[7] >= 0
 wire_group22_constraint: - x[22] + y[1] + y[12] + z[3] >= 0
 wire_group23_constraint: - x[23] + z[6] >= 0
 wire_group27_constraint: - x[27] + y[19] >= 0
 cell_0_input_group5_constraint: x[5] - y[0] >= 0
 cell_0_input_group16_constraint: x[16] - y[0] >= 0
 cell_1_input_group23_constraint: x[23] - y[1] >= 0
 cell_1_input_group3_constraint: x[3] - y[1] >= 0
 cell_2_input_group25_constraint: x[25] - y[2] >= 0
 cell_2_input_group24_constraint: x[24] - y[2] >= 0
 cell_2_input_group26_constraint: x[26] - y[2] >= 0
 cell_2_input_group13_constraint: x[13] - y[2] >= 0
 cell_3_input_group10_constraint: x[10] - y[3] >= 0
 cell_3_input_group15_constraint: x[15] - y[3] >= 0
 cell_4_input_group25_constraint: x[25] - y[4] >= 0
 cell_4_input_group1_constraint: x[1] - y[4] >= 0
 cell_5_input_group25_constraint: x[25] - y[5] >= 0
 cell_5_input_group11_constraint: x[11] - y[5] >= 0
 cell_6_input_group25_constraint: x[25] - y[6] >= 0
 cell_6_input_group24_constraint: x[24] - y[6] >= 0
 cell_7_input_group5_constraint: x[5] - y[7] >= 0
 cell_7_input_group2_constraint: x[2] - y[7] >= 0
 cell_8_input_group17_constraint: x[17] - y[8] >= 0
 cell_8_input_group14_constraint: x[14] - y[8] >= 0
 cell_9_input_group24_constraint: x[24] - y[9] >= 0
 cell_9_input_group1_constraint: x[1] - y[9] >= 0
 cell_10_input_group0_constraint: x[0] - y[10] >= 0
 cell_10_input_group18_constraint: x[18] - y[10] >= 0
 cell_11_input_group13_constraint: x[13] - y[11] >= 0
 cell_11_input_group1_constraint: x[1] - y[11] >= 0
 cell_12_input_group6_constraint: x[6] - y[12] >= 0
 cell_12_input_group14_constraint: x[14] - y[12] >= 0
 cell_13_input_group27_constraint: x[27] - y[13] >= 0
 cell_13_input_group24_constraint: x[24] - y[13] >= 0
 cell_14_input_group20_constraint: x[20] - y[14] >= 0
 cell_14_input_group7_constraint: x[7] - y[14] >= 0
 cell_15_input_group1_constraint: x[1] - y[15] >= 0
 cell_15_input_group25_constraint: x[25] - y[15] >= 0
 cell_15_input_group26_constraint: x[26] - y[15] >= 0
 cell_15_input_group13_constraint: x[13] - y[15] >= 0
 cell_16_input_group13_constraint: x[13] - y[16] >= 0
 cell_16_input_group25_constraint: x[25] - y[16] >= 0
 cell_17_input_group13_constraint: x[13] - y[17] >= 0
 cell_17_input_group4_constraint: x[4] - y[17] >= 0
 cell_18_input_group13_constraint: x[13] - y[18] >= 0
 cell_18_input_group24_constraint: x[24] - y[18] >= 0
 cell_19_input_group13_constraint: x[13] - y[19] >= 0
 cell_19_input_group1_constraint: x[1] - y[19] >= 0
 dff_0_input_group9_constraint: x[9] - z[0] >= 0
 dff_0_clk_group26_constraint: x[26] - z[0] >= 0
 dff_1_input_group22_constraint: x[22] - z[1] >= 0
 dff_1_clk_group26_constraint: x[26] - z[1] >= 0
 dff_2_input_group12_constraint: x[12] - z[2] >= 0
 dff_2_clk_group26_constraint: x[26] - z[2] >= 0
 dff_3_input_group21_constraint: x[21] - z[3] >= 0
 dff_3_clk_group26_constraint: x[26] - z[3] >= 0
 dff_4_input_group16_constraint: x[16] - z[4] >= 0
 dff_4_clk_group26_constraint: x[26] - z[4] >= 0
 dff_5_input_group15_constraint: x[15] - z[5] >= 0
 dff_5_clk_group26_constraint: x[26] - z[5] >= 0
 dff_6_input_group10_constraint: x[10] - z[6] >= 0
 dff_6_clk_group26_constraint: x[26] - z[6] >= 0
 dff_7_input_group0_constraint: x[0] - z[7] >= 0
 dff_7_clk_group26_constraint: x[26] - z[7] >= 0
 dff_8_input_group18_constraint: x[18] - z[8] >= 0
 dff_8_clk_group26_constraint: x[26] - z[8] >= 0
Bounds
Binaries
 x[0] x[1] x[2] x[3] x[4] x[5] x[6] x[7] x[8] x[9] x[10] x[11] x[12] x[13]
 x[14] x[15] x[16] x[17] x[18] x[19] x[20] x[21] x[22] x[23] x[24] x[25]
 x[26] x[27] y[0] y[1] y[2] y[3] y[4] y[5] y[6] y[7] y[8] y[9] y[10] y[11]
 y[12] y[13] y[14] y[15] y[16] y[17] y[18] y[19] z[0] z[1] z[2] z[3] z[4]
 z[5] z[6] z[7] z[8]
End
