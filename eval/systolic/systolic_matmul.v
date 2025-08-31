module top (
	clk,
	acc_rst,
	a,
	b,
	c
);
	reg _sv2v_0;
	parameter signed [31:0] MATRIX_SIZE = 4;
	parameter signed [31:0] DIN_WIDTH = 8;
	parameter signed [31:0] DOUT_WIDTH = DIN_WIDTH;
	input wire clk;
	input wire [(MATRIX_SIZE * MATRIX_SIZE) - 1:0] acc_rst;
	input wire signed [(MATRIX_SIZE * DIN_WIDTH) - 1:0] a;
	input wire signed [(MATRIX_SIZE * DIN_WIDTH) - 1:0] b;
	output wire signed [((MATRIX_SIZE * MATRIX_SIZE) * DOUT_WIDTH) - 1:0] c;
	reg signed [DIN_WIDTH - 1:0] a_reg [0:(MATRIX_SIZE * MATRIX_SIZE) - 1];
	reg signed [DIN_WIDTH - 1:0] b_reg [0:(MATRIX_SIZE * MATRIX_SIZE) - 1];
	reg signed [DOUT_WIDTH - 1:0] c_reg [0:(MATRIX_SIZE * MATRIX_SIZE) - 1];
	reg signed [DIN_WIDTH - 1:0] a_cur [0:(MATRIX_SIZE * MATRIX_SIZE) - 1];
	reg signed [DIN_WIDTH - 1:0] b_cur [0:(MATRIX_SIZE * MATRIX_SIZE) - 1];
	reg signed [DOUT_WIDTH - 1:0] c_cur [0:(MATRIX_SIZE * MATRIX_SIZE) - 1];
	genvar _gv_gi_1;
	generate
		for (_gv_gi_1 = 0; _gv_gi_1 < (MATRIX_SIZE * MATRIX_SIZE); _gv_gi_1 = _gv_gi_1 + 1) begin : GEN_OUT
			localparam gi = _gv_gi_1;
			assign c[(((MATRIX_SIZE * MATRIX_SIZE) - 1) - gi) * DOUT_WIDTH+:DOUT_WIDTH] = c_reg[gi];
		end
	endgenerate
	genvar _gv_i_1;
	genvar _gv_j_1;
	generate
		for (_gv_i_1 = 0; _gv_i_1 < MATRIX_SIZE; _gv_i_1 = _gv_i_1 + 1) begin : ROW
			localparam i = _gv_i_1;
			for (_gv_j_1 = 0; _gv_j_1 < MATRIX_SIZE; _gv_j_1 = _gv_j_1 + 1) begin : COL
				localparam j = _gv_j_1;
				always @(*) begin
					if (_sv2v_0)
						;
					if (i == 0)
						b_cur[(i * MATRIX_SIZE) + j] = b[((MATRIX_SIZE - 1) - j) * DIN_WIDTH+:DIN_WIDTH];
					else
						b_cur[(i * MATRIX_SIZE) + j] = b_reg[((i - 1) * MATRIX_SIZE) + j];
					if (j == 0)
						a_cur[(i * MATRIX_SIZE) + j] = a[((MATRIX_SIZE - 1) - i) * DIN_WIDTH+:DIN_WIDTH];
					else
						a_cur[(i * MATRIX_SIZE) + j] = a_reg[(i * MATRIX_SIZE) + (j - 1)];
					if (acc_rst[(i * MATRIX_SIZE) + j])
						c_cur[(i * MATRIX_SIZE) + j] = 1'sb0;
					else
						c_cur[(i * MATRIX_SIZE) + j] = c_reg[(i * MATRIX_SIZE) + j];
				end
			end
		end
	endgenerate
	always @(posedge clk) begin : sv2v_autoblock_1
		reg signed [31:0] i;
		for (i = 0; i < MATRIX_SIZE; i = i + 1)
			begin : sv2v_autoblock_2
				reg signed [31:0] j;
				for (j = 0; j < MATRIX_SIZE; j = j + 1)
					begin : sv2v_autoblock_3
						reg signed [31:0] idx;
						idx = (i * MATRIX_SIZE) + j;
						c_reg[idx] <= c_cur[idx] + (a_cur[idx] * b_cur[idx]);
						a_reg[idx] <= a_cur[idx];
						b_reg[idx] <= b_cur[idx];
					end
			end
	end
	initial _sv2v_0 = 0;
endmodule