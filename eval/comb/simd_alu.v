// simd_alu.v
// Parameterizable SIMD ALU (combinational).
// Each lane = WIDTH / LANES bits, supports basic logic & arithmetic.
// Opcodes (per lane):
// 4'b0000: ADD
// 4'b0001: SUB
// 4'b0010: AND
// 4'b0011: OR
// 4'b0100: XOR
// 4'b0101: MUL (lower bits only)
// 4'b0110: SLT (signed <)
// 4'b0111: SLTU (unsigned <)
// 4'b1111: PASS A
// others : 0

module simd_alu #(
    parameter WIDTH = 32,
    parameter LANES = 4
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire [3:0]       opcode,
    output wire [WIDTH-1:0] result
);

    localparam LANE_WIDTH = WIDTH / LANES;

    // sanity check
    initial begin
        if (WIDTH % LANES != 0) begin
            $error("WIDTH (%0d) must be divisible by LANES (%0d)", WIDTH, LANES);
        end
    end

    genvar i;
    generate
        for (i = 0; i < LANES; i = i + 1) begin : lane
            wire [LANE_WIDTH-1:0] a_lane = a[i*LANE_WIDTH +: LANE_WIDTH];
            wire [LANE_WIDTH-1:0] b_lane = b[i*LANE_WIDTH +: LANE_WIDTH];
            reg  [LANE_WIDTH-1:0] r_lane;

            wire signed [LANE_WIDTH-1:0] a_s = a_lane;
            wire signed [LANE_WIDTH-1:0] b_s = b_lane;

            always @* begin
                r_lane = {LANE_WIDTH{1'b0}};
                case (opcode)
                    4'b0000: r_lane = a_lane + b_lane;         // ADD
                    4'b0001: r_lane = a_lane - b_lane;         // SUB
                    4'b0010: r_lane = a_lane & b_lane;         // AND
                    4'b0011: r_lane = a_lane | b_lane;         // OR
                    4'b0100: r_lane = a_lane ^ b_lane;         // XOR
                    4'b0101: r_lane = (a_lane * b_lane);       // MUL (lower bits)
                    4'b0110: r_lane = (a_s < b_s) ? 1 : 0;     // SLT signed
                    4'b0111: r_lane = (a_lane < b_lane) ? 1 : 0; // SLTU unsigned
                    4'b1111: r_lane = a_lane;                  // PASS A
                    default: r_lane = {LANE_WIDTH{1'b0}};
                endcase
            end

            assign result[i*LANE_WIDTH +: LANE_WIDTH] = r_lane;
        end
    endgenerate

endmodule
