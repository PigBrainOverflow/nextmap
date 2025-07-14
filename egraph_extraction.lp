\ Model egraph_extraction
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  256 y[0] + 64 y[1] + 256 y[2] + 256 y[3] + 256 y[4] + 64 y[5] + 256 y[7]
   + 64 y[8] + 256 y[9] + 256 y[10] + 256 y[11] + 256 y[13] + 64 y[14]
   + 64 y[15] + 256 y[16] + 256 y[17] + 256 y[19] + 64 y[21] + 64 y[22]
   + 32 y[23] + 256 y[24] + 32 y[25] + 256 y[27] + 64 y[29] + 256 y[30]
   + 64 y[31] + 256 y[32] + 256 y[34] + 32 y[35] + 256 y[36] + 32 y[38]
   + 32 y[39] + 64 y[40] + 256 y[41] + 256 y[43] + 256 y[44] + 256 y[46]
   + 256 y[47] + 32 y[48] + 64 y[49] + 256 y[50] + 256 y[53] + 256 y[54]
   + 64 y[55] + 32 y[56] + 256 y[57] + 64 y[59] + 256 y[60] + 256 y[61]
   + 64 y[62] + 32 y[63] + 32 y[64] + 256 y[65] + 64 y[66] + 64 y[67]
   + 32 y[68] + 64 y[69] + 256 y[71] + 256 y[72] + 64 y[73] + 256 y[74]
   + 256 y[75] + 32 y[76] + 64 y[78] + 256 y[79] + 64 y[81] + 256 y[82]
   + 256 y[83] + 32 y[84] + 256 y[85] + 256 y[86] + 256 y[87] + 64 y[89]
   + 256 y[91] + 256 y[92] + 16 z[0] + 16 z[1] + 16 z[2] + 16 z[3]
   + 16 z[4] + 16 z[5] + 16 z[6] + 16 z[7] + 16 z[8] + 16 z[9] + 16 z[10]
   + 16 z[11] + 16 z[12] + 16 z[13] + 16 z[14] + 16 z[15] + 8 z[16]
   + 8 z[17] + 8 z[18] + 8 z[19] + 8 z[20] + 8 z[21] + 8 z[22] + 16 z[23]
   + 16 z[24] + 8 z[25] + 8 z[26] + 8 z[27] + 8 z[28] + 8 z[29] + 8 z[30]
   + 8 z[31]
Subject To
 output_group22_constraint: x[22] >= 1
 output_group16_constraint: x[16] >= 1
 wire_group0_constraint: - x[0] + y[17] + y[36] >= 0
 wire_group1_constraint: - x[1] + z[29] >= 0
 wire_group2_constraint: - x[2] + y[39] + z[18] >= 0
 wire_group3_constraint: - x[3] + z[28] >= 0
 wire_group4_constraint: - x[4] + z[17] >= 0
 wire_group5_constraint: - x[5] + y[4] + y[71] >= 0
 wire_group6_constraint: - x[6] + y[34] + y[53] + z[8] >= 0
 wire_group7_constraint: - x[7] + y[44] + y[47] + y[70] + z[12] >= 0
 wire_group8_constraint: - x[8] + y[23] + y[76] + z[30] >= 0
 wire_group9_constraint: - x[9] + y[32] + y[86] >= 0
 wire_group11_constraint: - x[11] + y[61] + y[79] + z[24] >= 0
 wire_group12_constraint: - x[12] + y[46] + y[50] + y[77] + z[5] >= 0
 wire_group13_constraint: - x[13] + y[54] + y[72] + z[23] >= 0
 wire_group14_constraint: - x[14] + y[13] + y[41] >= 0
 wire_group15_constraint: - x[15] + y[62] + y[69] + y[80] + y[81] + y[88]
   + y[89] + z[3] >= 0
 wire_group16_constraint: - x[16] + y[18] + y[49] + y[51] + y[52] + y[66]
   + y[67] + z[0] >= 0
 wire_group17_constraint: - x[17] + y[7] + y[16] + z[7] >= 0
 wire_group18_constraint: - x[18] + y[27] + y[30] + z[15] >= 0
 wire_group20_constraint: - x[20] + y[68] + z[16] >= 0
 wire_group21_constraint: - x[21] + z[26] >= 0
 wire_group22_constraint: - x[22] + y[5] + y[8] + y[12] + y[14] + y[15]
   + y[20] + z[1] >= 0
 wire_group23_constraint: - x[23] + z[31] >= 0
 wire_group24_constraint: - x[24] + y[43] + y[65] >= 0
 wire_group26_constraint: - x[26] + y[1] + y[40] + y[55] + y[73] >= 0
 wire_group27_constraint: - x[27] + y[10] + y[87] >= 0
 wire_group28_constraint: - x[28] + y[26] + y[28] + y[29] + y[31] + y[58]
   + y[59] + z[2] >= 0
 wire_group29_constraint: - x[29] + y[85] + y[91] + z[10] >= 0
 wire_group30_constraint: - x[30] + y[21] + y[22] + y[78] >= 0
 wire_group31_constraint: - x[31] + y[0] + y[3] >= 0
 wire_group32_constraint: - x[32] + y[11] + y[83] + z[14] >= 0
 wire_group33_constraint: - x[33] + y[6] + y[24] + y[45] + y[82] + z[6]
   >= 0
 wire_group34_constraint: - x[34] + y[57] + y[60] + z[9] >= 0
 wire_group35_constraint: - x[35] + y[19] + y[37] + y[90] + y[92] + z[13]
   >= 0
 wire_group36_constraint: - x[36] + z[21] >= 0
 wire_group37_constraint: - x[37] + y[35] >= 0
 wire_group38_constraint: - x[38] + y[9] + y[42] + y[74] + z[4] >= 0
 wire_group40_constraint: - x[40] + y[25] >= 0
 wire_group41_constraint: - x[41] + y[2] + y[33] + y[75] + z[11] >= 0
 wire_group42_constraint: - x[42] + z[19] >= 0
 wire_group43_constraint: - x[43] + y[84] + z[27] >= 0
 wire_group44_constraint: - x[44] + y[63] + y[64] >= 0
 wire_group45_constraint: - x[45] + z[22] >= 0
 wire_group46_constraint: - x[46] + y[38] + y[56] + z[20] >= 0
 wire_group47_constraint: - x[47] + y[48] + z[25] >= 0
 cell_0_input_group37_constraint: x[37] - y[0] >= 0
 cell_0_input_group39_constraint: x[39] - y[0] >= 0
 cell_1_input_group27_constraint: x[27] - y[1] >= 0
 cell_1_input_group24_constraint: x[24] - y[1] >= 0
 cell_2_input_group47_constraint: x[47] - y[2] >= 0
 cell_2_input_group21_constraint: x[21] - y[2] >= 0
 cell_3_input_group37_constraint: x[37] - y[3] >= 0
 cell_3_input_group39_constraint: x[39] - y[3] >= 0
 cell_4_input_group39_constraint: x[39] - y[4] >= 0
 cell_4_input_group19_constraint: x[19] - y[4] >= 0
 cell_5_input_group41_constraint: x[41] - y[5] >= 0
 cell_5_input_group7_constraint: x[7] - y[5] >= 0
 cell_6_input_group25_constraint: x[25] - y[6] >= 0
 cell_6_input_group10_constraint: x[10] - y[6] >= 0
 cell_6_input_group19_constraint: x[19] - y[6] >= 0
 cell_6_input_group48_constraint: x[48] - y[6] >= 0
 cell_7_input_group42_constraint: x[42] - y[7] >= 0
 cell_7_input_group4_constraint: x[4] - y[7] >= 0
 cell_8_input_group41_constraint: x[41] - y[8] >= 0
 cell_8_input_group7_constraint: x[7] - y[8] >= 0
 cell_9_input_group4_constraint: x[4] - y[9] >= 0
 cell_9_input_group20_constraint: x[20] - y[9] >= 0
 cell_10_input_group25_constraint: x[25] - y[10] >= 0
 cell_10_input_group19_constraint: x[19] - y[10] >= 0
 cell_11_input_group3_constraint: x[3] - y[11] >= 0
 cell_11_input_group21_constraint: x[21] - y[11] >= 0
 cell_12_input_group36_constraint: x[36] - y[12] >= 0
 cell_12_input_group48_constraint: x[48] - y[12] >= 0
 cell_12_input_group42_constraint: x[42] - y[12] >= 0
 cell_12_input_group4_constraint: x[4] - y[12] >= 0
 cell_12_input_group12_constraint: x[12] - y[12] >= 0
 cell_13_input_group44_constraint: x[44] - y[13] >= 0
 cell_13_input_group25_constraint: x[25] - y[13] >= 0
 cell_14_input_group18_constraint: x[18] - y[14] >= 0
 cell_14_input_group32_constraint: x[32] - y[14] >= 0
 cell_15_input_group18_constraint: x[18] - y[15] >= 0
 cell_15_input_group32_constraint: x[32] - y[15] >= 0
 cell_16_input_group42_constraint: x[42] - y[16] >= 0
 cell_16_input_group4_constraint: x[4] - y[16] >= 0
 cell_17_input_group25_constraint: x[25] - y[17] >= 0
 cell_17_input_group10_constraint: x[10] - y[17] >= 0
 cell_18_input_group45_constraint: x[45] - y[18] >= 0
 cell_18_input_group38_constraint: x[38] - y[18] >= 0
 cell_18_input_group36_constraint: x[36] - y[18] >= 0
 cell_18_input_group48_constraint: x[48] - y[18] >= 0
 cell_18_input_group4_constraint: x[4] - y[18] >= 0
 cell_19_input_group23_constraint: x[23] - y[19] >= 0
 cell_19_input_group8_constraint: x[8] - y[19] >= 0
 cell_20_input_group45_constraint: x[45] - y[20] >= 0
 cell_20_input_group38_constraint: x[38] - y[20] >= 0
 cell_20_input_group48_constraint: x[48] - y[20] >= 0
 cell_20_input_group42_constraint: x[42] - y[20] >= 0
 cell_20_input_group4_constraint: x[4] - y[20] >= 0
 cell_21_input_group14_constraint: x[14] - y[21] >= 0
 cell_21_input_group9_constraint: x[9] - y[21] >= 0
 cell_22_input_group14_constraint: x[14] - y[22] >= 0
 cell_22_input_group9_constraint: x[9] - y[22] >= 0
 cell_23_input_group1_constraint: x[1] - y[23] >= 0
 cell_23_input_group21_constraint: x[21] - y[23] >= 0
 cell_24_input_group46_constraint: x[46] - y[24] >= 0
 cell_24_input_group36_constraint: x[36] - y[24] >= 0
 cell_25_input_group39_constraint: x[39] - y[25] >= 0
 cell_25_input_group25_constraint: x[25] - y[25] >= 0
 cell_26_input_group19_constraint: x[19] - y[26] >= 0
 cell_26_input_group9_constraint: x[9] - y[26] >= 0
 cell_26_input_group25_constraint: x[25] - y[26] >= 0
 cell_26_input_group48_constraint: x[48] - y[26] >= 0
 cell_26_input_group10_constraint: x[10] - y[26] >= 0
 cell_27_input_group23_constraint: x[23] - y[27] >= 0
 cell_27_input_group1_constraint: x[1] - y[27] >= 0
 cell_28_input_group14_constraint: x[14] - y[28] >= 0
 cell_28_input_group39_constraint: x[39] - y[28] >= 0
 cell_28_input_group25_constraint: x[25] - y[28] >= 0
 cell_28_input_group48_constraint: x[48] - y[28] >= 0
 cell_28_input_group10_constraint: x[10] - y[28] >= 0
 cell_29_input_group33_constraint: x[33] - y[29] >= 0
 cell_29_input_group38_constraint: x[38] - y[29] >= 0
 cell_30_input_group23_constraint: x[23] - y[30] >= 0
 cell_30_input_group1_constraint: x[1] - y[30] >= 0
 cell_31_input_group33_constraint: x[33] - y[31] >= 0
 cell_31_input_group38_constraint: x[38] - y[31] >= 0
 cell_32_input_group10_constraint: x[10] - y[32] >= 0
 cell_32_input_group40_constraint: x[40] - y[32] >= 0
 cell_33_input_group48_constraint: x[48] - y[33] >= 0
 cell_33_input_group4_constraint: x[4] - y[33] >= 0
 cell_33_input_group42_constraint: x[42] - y[33] >= 0
 cell_33_input_group36_constraint: x[36] - y[33] >= 0
 cell_34_input_group36_constraint: x[36] - y[34] >= 0
 cell_34_input_group45_constraint: x[45] - y[34] >= 0
 cell_35_input_group10_constraint: x[10] - y[35] >= 0
 cell_35_input_group19_constraint: x[19] - y[35] >= 0
 cell_36_input_group25_constraint: x[25] - y[36] >= 0
 cell_36_input_group10_constraint: x[10] - y[36] >= 0
 cell_37_input_group4_constraint: x[4] - y[37] >= 0
 cell_37_input_group36_constraint: x[36] - y[37] >= 0
 cell_37_input_group48_constraint: x[48] - y[37] >= 0
 cell_37_input_group45_constraint: x[45] - y[37] >= 0
 cell_38_input_group4_constraint: x[4] - y[38] >= 0
 cell_38_input_group45_constraint: x[45] - y[38] >= 0
 cell_39_input_group4_constraint: x[4] - y[39] >= 0
 cell_39_input_group45_constraint: x[45] - y[39] >= 0
 cell_40_input_group27_constraint: x[27] - y[40] >= 0
 cell_40_input_group24_constraint: x[24] - y[40] >= 0
 cell_41_input_group44_constraint: x[44] - y[41] >= 0
 cell_41_input_group25_constraint: x[25] - y[41] >= 0
 cell_42_input_group25_constraint: x[25] - y[42] >= 0
 cell_42_input_group10_constraint: x[10] - y[42] >= 0
 cell_42_input_group48_constraint: x[48] - y[42] >= 0
 cell_42_input_group39_constraint: x[39] - y[42] >= 0
 cell_43_input_group39_constraint: x[39] - y[43] >= 0
 cell_43_input_group10_constraint: x[10] - y[43] >= 0
 cell_44_input_group3_constraint: x[3] - y[44] >= 0
 cell_44_input_group43_constraint: x[43] - y[44] >= 0
 cell_45_input_group25_constraint: x[25] - y[45] >= 0
 cell_45_input_group10_constraint: x[10] - y[45] >= 0
 cell_45_input_group19_constraint: x[19] - y[45] >= 0
 cell_45_input_group48_constraint: x[48] - y[45] >= 0
 cell_46_input_group42_constraint: x[42] - y[46] >= 0
 cell_46_input_group2_constraint: x[2] - y[46] >= 0
 cell_47_input_group3_constraint: x[3] - y[47] >= 0
 cell_47_input_group43_constraint: x[43] - y[47] >= 0
 cell_48_input_group3_constraint: x[3] - y[48] >= 0
 cell_48_input_group23_constraint: x[23] - y[48] >= 0
 cell_49_input_group35_constraint: x[35] - y[49] >= 0
 cell_49_input_group41_constraint: x[41] - y[49] >= 0
 cell_50_input_group42_constraint: x[42] - y[50] >= 0
 cell_50_input_group2_constraint: x[2] - y[50] >= 0
 cell_51_input_group45_constraint: x[45] - y[51] >= 0
 cell_51_input_group38_constraint: x[38] - y[51] >= 0
 cell_51_input_group36_constraint: x[36] - y[51] >= 0
 cell_51_input_group48_constraint: x[48] - y[51] >= 0
 cell_51_input_group4_constraint: x[4] - y[51] >= 0
 cell_52_input_group33_constraint: x[33] - y[52] >= 0
 cell_52_input_group36_constraint: x[36] - y[52] >= 0
 cell_52_input_group48_constraint: x[48] - y[52] >= 0
 cell_52_input_group42_constraint: x[42] - y[52] >= 0
 cell_52_input_group4_constraint: x[4] - y[52] >= 0
 cell_53_input_group36_constraint: x[36] - y[53] >= 0
 cell_53_input_group45_constraint: x[45] - y[53] >= 0
 cell_54_input_group1_constraint: x[1] - y[54] >= 0
 cell_54_input_group3_constraint: x[3] - y[54] >= 0
 cell_55_input_group31_constraint: x[31] - y[55] >= 0
 cell_55_input_group9_constraint: x[9] - y[55] >= 0
 cell_56_input_group4_constraint: x[4] - y[56] >= 0
 cell_56_input_group45_constraint: x[45] - y[56] >= 0
 cell_57_input_group45_constraint: x[45] - y[57] >= 0
 cell_57_input_group42_constraint: x[42] - y[57] >= 0
 cell_58_input_group19_constraint: x[19] - y[58] >= 0
 cell_58_input_group9_constraint: x[9] - y[58] >= 0
 cell_58_input_group25_constraint: x[25] - y[58] >= 0
 cell_58_input_group48_constraint: x[48] - y[58] >= 0
 cell_58_input_group10_constraint: x[10] - y[58] >= 0
 cell_59_input_group34_constraint: x[34] - y[59] >= 0
 cell_59_input_group29_constraint: x[29] - y[59] >= 0
 cell_60_input_group45_constraint: x[45] - y[60] >= 0
 cell_60_input_group42_constraint: x[42] - y[60] >= 0
 cell_61_input_group23_constraint: x[23] - y[61] >= 0
 cell_61_input_group21_constraint: x[21] - y[61] >= 0
 cell_62_input_group12_constraint: x[12] - y[62] >= 0
 cell_62_input_group38_constraint: x[38] - y[62] >= 0
 cell_63_input_group10_constraint: x[10] - y[63] >= 0
 cell_63_input_group19_constraint: x[19] - y[63] >= 0
 cell_64_input_group10_constraint: x[10] - y[64] >= 0
 cell_64_input_group19_constraint: x[19] - y[64] >= 0
 cell_65_input_group39_constraint: x[39] - y[65] >= 0
 cell_65_input_group10_constraint: x[10] - y[65] >= 0
 cell_66_input_group35_constraint: x[35] - y[66] >= 0
 cell_66_input_group41_constraint: x[41] - y[66] >= 0
 cell_67_input_group11_constraint: x[11] - y[67] >= 0
 cell_67_input_group13_constraint: x[13] - y[67] >= 0
 cell_68_input_group42_constraint: x[42] - y[68] >= 0
 cell_68_input_group36_constraint: x[36] - y[68] >= 0
 cell_69_input_group17_constraint: x[17] - y[69] >= 0
 cell_69_input_group6_constraint: x[6] - y[69] >= 0
 cell_70_input_group4_constraint: x[4] - y[70] >= 0
 cell_70_input_group48_constraint: x[48] - y[70] >= 0
 cell_70_input_group45_constraint: x[45] - y[70] >= 0
 cell_70_input_group42_constraint: x[42] - y[70] >= 0
 cell_71_input_group39_constraint: x[39] - y[71] >= 0
 cell_71_input_group19_constraint: x[19] - y[71] >= 0
 cell_72_input_group1_constraint: x[1] - y[72] >= 0
 cell_72_input_group3_constraint: x[3] - y[72] >= 0
 cell_73_input_group31_constraint: x[31] - y[73] >= 0
 cell_73_input_group9_constraint: x[9] - y[73] >= 0
 cell_74_input_group4_constraint: x[4] - y[74] >= 0
 cell_74_input_group20_constraint: x[20] - y[74] >= 0
 cell_75_input_group47_constraint: x[47] - y[75] >= 0
 cell_75_input_group21_constraint: x[21] - y[75] >= 0
 cell_76_input_group1_constraint: x[1] - y[76] >= 0
 cell_76_input_group21_constraint: x[21] - y[76] >= 0
 cell_77_input_group10_constraint: x[10] - y[77] >= 0
 cell_77_input_group19_constraint: x[19] - y[77] >= 0
 cell_77_input_group48_constraint: x[48] - y[77] >= 0
 cell_77_input_group39_constraint: x[39] - y[77] >= 0
 cell_78_input_group0_constraint: x[0] - y[78] >= 0
 cell_78_input_group5_constraint: x[5] - y[78] >= 0
 cell_79_input_group23_constraint: x[23] - y[79] >= 0
 cell_79_input_group21_constraint: x[21] - y[79] >= 0
 cell_80_input_group39_constraint: x[39] - y[80] >= 0
 cell_80_input_group25_constraint: x[25] - y[80] >= 0
 cell_80_input_group31_constraint: x[31] - y[80] >= 0
 cell_80_input_group48_constraint: x[48] - y[80] >= 0
 cell_80_input_group10_constraint: x[10] - y[80] >= 0
 cell_81_input_group12_constraint: x[12] - y[81] >= 0
 cell_81_input_group38_constraint: x[38] - y[81] >= 0
 cell_82_input_group46_constraint: x[46] - y[82] >= 0
 cell_82_input_group36_constraint: x[36] - y[82] >= 0
 cell_83_input_group3_constraint: x[3] - y[83] >= 0
 cell_83_input_group21_constraint: x[21] - y[83] >= 0
 cell_84_input_group1_constraint: x[1] - y[84] >= 0
 cell_84_input_group21_constraint: x[21] - y[84] >= 0
 cell_85_input_group4_constraint: x[4] - y[85] >= 0
 cell_85_input_group36_constraint: x[36] - y[85] >= 0
 cell_86_input_group10_constraint: x[10] - y[86] >= 0
 cell_86_input_group40_constraint: x[40] - y[86] >= 0
 cell_87_input_group25_constraint: x[25] - y[87] >= 0
 cell_87_input_group19_constraint: x[19] - y[87] >= 0
 cell_88_input_group19_constraint: x[19] - y[88] >= 0
 cell_88_input_group39_constraint: x[39] - y[88] >= 0
 cell_88_input_group9_constraint: x[9] - y[88] >= 0
 cell_88_input_group48_constraint: x[48] - y[88] >= 0
 cell_88_input_group10_constraint: x[10] - y[88] >= 0
 cell_89_input_group17_constraint: x[17] - y[89] >= 0
 cell_89_input_group6_constraint: x[6] - y[89] >= 0
 cell_90_input_group4_constraint: x[4] - y[90] >= 0
 cell_90_input_group36_constraint: x[36] - y[90] >= 0
 cell_90_input_group48_constraint: x[48] - y[90] >= 0
 cell_90_input_group45_constraint: x[45] - y[90] >= 0
 cell_91_input_group4_constraint: x[4] - y[91] >= 0
 cell_91_input_group36_constraint: x[36] - y[91] >= 0
 cell_92_input_group23_constraint: x[23] - y[92] >= 0
 cell_92_input_group8_constraint: x[8] - y[92] >= 0
 dff_0_input_group28_constraint: x[28] - z[0] >= 0
 dff_0_clk_group48_constraint: x[48] - z[0] >= 0
 dff_1_input_group15_constraint: x[15] - z[1] >= 0
 dff_1_clk_group48_constraint: x[48] - z[1] >= 0
 dff_2_input_group30_constraint: x[30] - z[2] >= 0
 dff_2_clk_group48_constraint: x[48] - z[2] >= 0
 dff_3_input_group26_constraint: x[26] - z[3] >= 0
 dff_3_clk_group48_constraint: x[48] - z[3] >= 0
 dff_4_input_group9_constraint: x[9] - z[4] >= 0
 dff_4_clk_group48_constraint: x[48] - z[4] >= 0
 dff_5_input_group31_constraint: x[31] - z[5] >= 0
 dff_5_clk_group48_constraint: x[48] - z[5] >= 0
 dff_6_input_group14_constraint: x[14] - z[6] >= 0
 dff_6_clk_group48_constraint: x[48] - z[6] >= 0
 dff_7_input_group24_constraint: x[24] - z[7] >= 0
 dff_7_clk_group48_constraint: x[48] - z[7] >= 0
 dff_8_input_group27_constraint: x[27] - z[8] >= 0
 dff_8_clk_group48_constraint: x[48] - z[8] >= 0
 dff_9_input_group5_constraint: x[5] - z[9] >= 0
 dff_9_clk_group48_constraint: x[48] - z[9] >= 0
 dff_10_input_group0_constraint: x[0] - z[10] >= 0
 dff_10_clk_group48_constraint: x[48] - z[10] >= 0
 dff_11_input_group38_constraint: x[38] - z[11] >= 0
 dff_11_clk_group48_constraint: x[48] - z[11] >= 0
 dff_12_input_group12_constraint: x[12] - z[12] >= 0
 dff_12_clk_group48_constraint: x[48] - z[12] >= 0
 dff_13_input_group33_constraint: x[33] - z[13] >= 0
 dff_13_clk_group48_constraint: x[48] - z[13] >= 0
 dff_14_input_group17_constraint: x[17] - z[14] >= 0
 dff_14_clk_group48_constraint: x[48] - z[14] >= 0
 dff_15_input_group6_constraint: x[6] - z[15] >= 0
 dff_15_clk_group48_constraint: x[48] - z[15] >= 0
 dff_16_input_group40_constraint: x[40] - z[16] >= 0
 dff_16_clk_group48_constraint: x[48] - z[16] >= 0
 dff_17_input_group10_constraint: x[10] - z[17] >= 0
 dff_17_clk_group48_constraint: x[48] - z[17] >= 0
 dff_18_input_group37_constraint: x[37] - z[18] >= 0
 dff_18_clk_group48_constraint: x[48] - z[18] >= 0
 dff_19_input_group39_constraint: x[39] - z[19] >= 0
 dff_19_clk_group48_constraint: x[48] - z[19] >= 0
 dff_20_input_group44_constraint: x[44] - z[20] >= 0
 dff_20_clk_group48_constraint: x[48] - z[20] >= 0
 dff_21_input_group25_constraint: x[25] - z[21] >= 0
 dff_21_clk_group48_constraint: x[48] - z[21] >= 0
 dff_22_input_group19_constraint: x[19] - z[22] >= 0
 dff_22_clk_group48_constraint: x[48] - z[22] >= 0
 dff_23_input_group34_constraint: x[34] - z[23] >= 0
 dff_23_clk_group48_constraint: x[48] - z[23] >= 0
 dff_24_input_group29_constraint: x[29] - z[24] >= 0
 dff_24_clk_group48_constraint: x[48] - z[24] >= 0
 dff_25_input_group20_constraint: x[20] - z[25] >= 0
 dff_25_clk_group48_constraint: x[48] - z[25] >= 0
 dff_26_input_group4_constraint: x[4] - z[26] >= 0
 dff_26_clk_group48_constraint: x[48] - z[26] >= 0
 dff_27_input_group2_constraint: x[2] - z[27] >= 0
 dff_27_clk_group48_constraint: x[48] - z[27] >= 0
 dff_28_input_group42_constraint: x[42] - z[28] >= 0
 dff_28_clk_group48_constraint: x[48] - z[28] >= 0
 dff_29_input_group45_constraint: x[45] - z[29] >= 0
 dff_29_clk_group48_constraint: x[48] - z[29] >= 0
 dff_30_input_group46_constraint: x[46] - z[30] >= 0
 dff_30_clk_group48_constraint: x[48] - z[30] >= 0
 dff_31_input_group36_constraint: x[36] - z[31] >= 0
 dff_31_clk_group48_constraint: x[48] - z[31] >= 0
 dsp_count_constraint: y[6] + y[12] + y[18] + y[20] + y[26] + y[28] + y[33]
   + y[37] + y[42] + y[45] + y[51] + y[52] + y[58] + y[70] + y[77] + y[80]
   + y[88] + y[90] <= 3
Bounds
Binaries
 x[0] x[1] x[2] x[3] x[4] x[5] x[6] x[7] x[8] x[9] x[10] x[11] x[12] x[13]
 x[14] x[15] x[16] x[17] x[18] x[19] x[20] x[21] x[22] x[23] x[24] x[25]
 x[26] x[27] x[28] x[29] x[30] x[31] x[32] x[33] x[34] x[35] x[36] x[37]
 x[38] x[39] x[40] x[41] x[42] x[43] x[44] x[45] x[46] x[47] x[48] y[0]
 y[1] y[2] y[3] y[4] y[5] y[6] y[7] y[8] y[9] y[10] y[11] y[12] y[13] y[14]
 y[15] y[16] y[17] y[18] y[19] y[20] y[21] y[22] y[23] y[24] y[25] y[26]
 y[27] y[28] y[29] y[30] y[31] y[32] y[33] y[34] y[35] y[36] y[37] y[38]
 y[39] y[40] y[41] y[42] y[43] y[44] y[45] y[46] y[47] y[48] y[49] y[50]
 y[51] y[52] y[53] y[54] y[55] y[56] y[57] y[58] y[59] y[60] y[61] y[62]
 y[63] y[64] y[65] y[66] y[67] y[68] y[69] y[70] y[71] y[72] y[73] y[74]
 y[75] y[76] y[77] y[78] y[79] y[80] y[81] y[82] y[83] y[84] y[85] y[86]
 y[87] y[88] y[89] y[90] y[91] y[92] z[0] z[1] z[2] z[3] z[4] z[5] z[6]
 z[7] z[8] z[9] z[10] z[11] z[12] z[13] z[14] z[15] z[16] z[17] z[18] z[19]
 z[20] z[21] z[22] z[23] z[24] z[25] z[26] z[27] z[28] z[29] z[30] z[31]
End
