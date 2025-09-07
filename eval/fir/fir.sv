module top #(
    parameter int N_TAPS = 64,
    parameter int COEF_WIDTH = 32,
    parameter int DIN_WIDTH = 32,
    parameter int DOUT_WIDTH = DIN_WIDTH+COEF_WIDTH
) (
    input logic clk,
    input logic reset,
    input logic signed [COEF_WIDTH-1:0] coef [N_TAPS-1:0],
    input logic signed [DIN_WIDTH-1] fir_data_in,
    output logic signed [DOUT_WIDTH-1:0] fir_data_out
);

    logic signed [COEF_WIDTH-1:0] coef_reg [N_TAPS-1:0];
    logic signed [DIN_WIDTH-1:0] buffer [N_TAPS-1:0];
    logic signed [DOUT_WIDTH-1:0] products [N_TAPS-1:0];
    logic signed [DOUT_WIDTH-1:0] sum;

    genvar i;
    generate
        for (i = 0; i < N_TAPS; i++) begin
            assign products[i] = buffer[i] * coef_reg[i];
        end
    endgenerate

    always_ff @(posedge clk) begin
        for (int k = 0; k < N_TAPS; k++) begin
            coef_reg[k] <= coef[k];
        end
        if (reset) begin
            for (int k = 0; k < N_TAPS; k++) begin
                buffer[k] <= '0;
            end
        end
        else begin
            buffer[0] <= fir_data_in;
            for (int k = 1; k < N_TAPS; k++) begin
                buffer[k] <= buffer[k-1];
            end
        end
    end

    always_comb begin
        sum = '0;
        for (int k = 0; k < N_TAPS; k++) begin
            sum = sum + products[k];
        end
    end

    assign fir_data_out = sum;

endmodule