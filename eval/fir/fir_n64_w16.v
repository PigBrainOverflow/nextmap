module top (
	clk,
	reset,
	coef,
	fir_data_in,
	fir_data_out
);
	reg _sv2v_0;
	parameter signed [31:0] N_TAPS = 64;
	parameter signed [31:0] COEF_WIDTH = 16;
	parameter signed [31:0] DIN_WIDTH = 16;
	parameter signed [31:0] DOUT_WIDTH = DIN_WIDTH + COEF_WIDTH;
	input wire clk;
	input wire reset;
	input wire signed [(N_TAPS * COEF_WIDTH) - 1:0] coef;
	input wire signed [0:DIN_WIDTH - 2] fir_data_in;
	output wire signed [DOUT_WIDTH - 1:0] fir_data_out;
	reg signed [COEF_WIDTH - 1:0] coef_reg [N_TAPS - 1:0];
	reg signed [DIN_WIDTH - 1:0] buffer [N_TAPS - 1:0];
	wire signed [DOUT_WIDTH - 1:0] products [N_TAPS - 1:0];
	reg signed [DOUT_WIDTH - 1:0] sum;
	genvar _gv_i_1;
	generate
		for (_gv_i_1 = 0; _gv_i_1 < N_TAPS; _gv_i_1 = _gv_i_1 + 1) begin : genblk1
			localparam i = _gv_i_1;
			assign products[i] = buffer[i] * coef_reg[i];
		end
	endgenerate
	always @(posedge clk) begin
		begin : sv2v_autoblock_1
			reg signed [31:0] k;
			for (k = 0; k < N_TAPS; k = k + 1)
				coef_reg[k] <= coef[k * COEF_WIDTH+:COEF_WIDTH];
		end
		if (reset) begin : sv2v_autoblock_2
			reg signed [31:0] k;
			for (k = 0; k < N_TAPS; k = k + 1)
				buffer[k] <= 1'sb0;
		end
		else begin
			buffer[0] <= fir_data_in;
			begin : sv2v_autoblock_3
				reg signed [31:0] k;
				for (k = 1; k < N_TAPS; k = k + 1)
					buffer[k] <= buffer[k - 1];
			end
		end
	end
	always @(*) begin
		if (_sv2v_0)
			;
		sum = 1'sb0;
		begin : sv2v_autoblock_4
			reg signed [31:0] k;
			for (k = 0; k < N_TAPS; k = k + 1)
				sum = sum + products[k];
		end
	end
	assign fir_data_out = sum;
	initial _sv2v_0 = 0;
endmodule