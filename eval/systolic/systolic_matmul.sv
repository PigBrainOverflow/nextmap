module top #(
    parameter int MATRIX_SIZE = 4,
    parameter int DIN_WIDTH   = 8,
    parameter int DOUT_WIDTH  = DIN_WIDTH
) (
    input  logic clk,

    // 1-bit reset per PE (flattened bus)
    input  logic [MATRIX_SIZE*MATRIX_SIZE-1:0] acc_rst,

    // matrix inputs
    input  logic signed [DIN_WIDTH-1:0] a [MATRIX_SIZE],
    input  logic signed [DIN_WIDTH-1:0] b [MATRIX_SIZE],

    // matrix output
    output logic signed [DOUT_WIDTH-1:0] c [MATRIX_SIZE*MATRIX_SIZE]
);

    // internal pipeline registers
    logic signed [DIN_WIDTH-1:0]  a_reg [MATRIX_SIZE*MATRIX_SIZE];
    logic signed [DIN_WIDTH-1:0]  b_reg [MATRIX_SIZE*MATRIX_SIZE];
    logic signed [DOUT_WIDTH-1:0] c_reg [MATRIX_SIZE*MATRIX_SIZE];

    // intermediate combinational values
    logic signed [DIN_WIDTH-1:0]  a_cur [MATRIX_SIZE*MATRIX_SIZE];
    logic signed [DIN_WIDTH-1:0]  b_cur [MATRIX_SIZE*MATRIX_SIZE];
    logic signed [DOUT_WIDTH-1:0] c_cur [MATRIX_SIZE*MATRIX_SIZE];

    // connect registered outputs
    genvar gi;
    generate
        for (gi = 0; gi < MATRIX_SIZE*MATRIX_SIZE; gi++) begin : GEN_OUT
            assign c[gi] = c_reg[gi];
        end
    endgenerate

    // combinational flow for each PE
    genvar i, j;
    generate
        for (i = 0; i < MATRIX_SIZE; i++) begin : ROW
            for (j = 0; j < MATRIX_SIZE; j++) begin : COL
                always_comb begin
                    // propagate b values downward
                    if (i == 0)
                        b_cur[i*MATRIX_SIZE+j] = b[j];
                    else
                        b_cur[i*MATRIX_SIZE+j] = b_reg[(i-1)*MATRIX_SIZE+j];

                    // propagate a values rightward
                    if (j == 0)
                        a_cur[i*MATRIX_SIZE+j] = a[i];
                    else
                        a_cur[i*MATRIX_SIZE+j] = a_reg[i*MATRIX_SIZE+(j-1)];

                    // reset or hold c
                    if (acc_rst[i*MATRIX_SIZE+j])
                        c_cur[i*MATRIX_SIZE+j] = '0;
                    else
                        c_cur[i*MATRIX_SIZE+j] = c_reg[i*MATRIX_SIZE+j];
                end
            end
        end
    endgenerate

    // sequential pipeline update
    always_ff @(posedge clk) begin
        for (int i = 0; i < MATRIX_SIZE; i++) begin
            for (int j = 0; j < MATRIX_SIZE; j++) begin
                int idx = i*MATRIX_SIZE + j;
                c_reg[idx] <= c_cur[idx] + a_cur[idx] * b_cur[idx];
                a_reg[idx] <= a_cur[idx];
                b_reg[idx] <= b_cur[idx];
            end
        end
    end

endmodule
