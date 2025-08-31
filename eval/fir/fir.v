module top (
	clk,
	reset,
	coef,
	fir_data_in,
	fir_data_out
);
	parameter signed [31:0] N_TAPS = 16;
	parameter signed [31:0] COEF_WIDTH = 16;
	parameter signed [31:0] DIN_WIDTH = 16;
	parameter signed [31:0] DOUT_WIDTH = DIN_WIDTH;
	input wire clk;
	input wire reset;
	input wire signed [(N_TAPS * COEF_WIDTH) - 1:0] coef;
	input wire signed [0:DIN_WIDTH - 2] fir_data_in;
	output reg signed [DOUT_WIDTH - 1:0] fir_data_out;
	reg signed [DIN_WIDTH - 1:0] buffer [N_TAPS - 1:0];
	wire signed [DOUT_WIDTH - 1:0] products [N_TAPS - 1:0];
	genvar _gv_i_1;
	generate
		for (_gv_i_1 = 0; _gv_i_1 < N_TAPS; _gv_i_1 = _gv_i_1 + 1) begin : MULT_STAGE
			localparam i = _gv_i_1;
			assign products[i] = buffer[i] * coef[i * COEF_WIDTH+:COEF_WIDTH];
		end
	endgenerate
	always @(posedge clk)
		if (reset) begin
			begin : sv2v_autoblock_1
				reg signed [31:0] k;
				for (k = 0; k < N_TAPS; k = k + 1)
					buffer[k] <= 1'sb0;
			end
			fir_data_out <= 1'sb0;
		end
		else begin
			buffer[0] <= fir_data_in;
			begin : sv2v_autoblock_2
				reg signed [31:0] k;
				for (k = 1; k < N_TAPS; k = k + 1)
					buffer[k] <= buffer[k - 1];
			end
			fir_data_out <= 1'sb0;
			begin : sv2v_autoblock_3
				reg signed [31:0] k;
				for (k = 0; k < N_TAPS; k = k + 1)
					fir_data_out <= fir_data_out + products[k];
			end
		end
endmodule