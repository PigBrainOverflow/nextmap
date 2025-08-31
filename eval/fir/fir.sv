module top #(
    parameter int N_TAPS = 16,
    parameter int COEF_WIDTH = 16,
    parameter int DIN_WIDTH = 16,
    parameter int DOUT_WIDTH = DIN_WIDTH
) (
    input logic clk,
    input logic reset,
    input logic signed [COEF_WIDTH-1:0] coef [N_TAPS-1:0],
    input logic signed [DIN_WIDTH-1] fir_data_in,
    output logic signed [DOUT_WIDTH-1:0] fir_data_out
);

    logic signed [DIN_WIDTH-1:0] buffer [N_TAPS-1:0];
    logic signed [DOUT_WIDTH-1:0] products [N_TAPS-1:0];

    genvar i;
    generate
        for (i = 0; i < N_TAPS; i++) begin : MULT_STAGE
            assign products[i] = buffer[i] * coef[i];
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (reset) begin
            for (int k = 0; k < N_TAPS; k++) begin
                buffer[k] <= '0;
            end
            fir_data_out <= '0;
        end
        else begin
            buffer[0] <= fir_data_in;
            for (int k = 1; k < N_TAPS; k++) begin
                buffer[k] <= buffer[k-1];
            end

            // accumulate products
            fir_data_out <= '0;
            for (int k = 0; k < N_TAPS; k++) begin
                fir_data_out <= fir_data_out + products[k];
            end
        end
    end

endmodule