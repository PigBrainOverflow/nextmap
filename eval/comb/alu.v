// comb_alu.v
// Purely combinational ALU: logic + arithmetic operations.
// Parameterizable width (default 32).
// Opcodes:
// 4'b0000: ADD
// 4'b0001: SUB
// 4'b0010: AND
// 4'b0011: OR
// 4'b0100: XOR
// 4'b0101: SLL (logical left)
// 4'b0110: SRL (logical right)
// 4'b0111: SRA (arithmetic right)
// 4'b1000: SLT (signed less-than -> 1 or 0)
// 4'b1001: SLTU (unsigned less-than -> 1 or 0)
// 4'b1010: MUL (lower WIDTH bits of product)
// 4'b1111: PASSA (result = a)
// others : result = 0

module alu #(
    parameter WIDTH = 32
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire [3:0]       opcode,
    output wire [WIDTH-1:0] result,
    output wire             zero,        // result == 0
    output wire             negative,    // MSB of result (signed negative)
    output wire             carry_out,   // carry/borrow for ADD/SUB (valid for those ops)
    output wire             overflow     // signed overflow for ADD/SUB
);

    // Intermediate wide product for MUL (combinational)
    wire [2*WIDTH-1:0] full_product = a * b;

    // ADD / SUB results with carry/overflow detection
    wire [WIDTH:0] add_ext = {1'b0, a} + {1'b0, b};                  // unsigned add with carry
    wire [WIDTH:0] sub_ext = {1'b0, a} - {1'b0, b};                  // unsigned sub with borrow in MSB

    // signed add/sub for overflow detection
    wire signed [WIDTH-1:0] a_s = a;
    wire signed [WIDTH-1:0] b_s = b;
    wire signed [WIDTH-1:0] add_s = a_s + b_s;
    wire signed [WIDTH-1:0] sub_s = a_s - b_s;

    // Selected combinational result
    reg [WIDTH-1:0] res_reg;
    reg carry_reg;
    reg overflow_reg;

    always @* begin
        // default
        res_reg     = {WIDTH{1'b0}};
        carry_reg   = 1'b0;
        overflow_reg= 1'b0;

        case (opcode)
            4'b0000: begin // ADD
                res_reg = add_ext[WIDTH-1:0];
                carry_reg = add_ext[WIDTH];
                // overflow: when signs of a and b same but sign of sum differs
                overflow_reg = (~a_s[WIDTH-1] & ~b_s[WIDTH-1] & add_s[WIDTH-1]) |
                               ( a_s[WIDTH-1] &  b_s[WIDTH-1] & ~add_s[WIDTH-1]);
            end
            4'b0001: begin // SUB (a - b)
                res_reg = sub_ext[WIDTH-1:0];
                carry_reg = ~sub_ext[WIDTH]; // borrow: if MSB of sub_ext is 1 => no borrow? keep as convention: carry_out = ~borrow
                // overflow for subtraction: signs differ and result sign differs from a
                overflow_reg = (a_s[WIDTH-1] & ~b_s[WIDTH-1] & ~sub_s[WIDTH-1]) |
                               (~a_s[WIDTH-1] &  b_s[WIDTH-1] & sub_s[WIDTH-1]);
            end
            4'b0010: res_reg = a & b;      // AND
            4'b0011: res_reg = a | b;      // OR
            4'b0100: res_reg = a ^ b;      // XOR
            4'b0101: res_reg = a << b[ $clog2(WIDTH)-1 : 0 ]; // SLL (shift amount width truncated)
            4'b0110: res_reg = a >> b[ $clog2(WIDTH)-1 : 0 ]; // SRL
            4'b0111: res_reg = $signed(a) >>> b[ $clog2(WIDTH)-1 : 0 ]; // SRA
            4'b1000: res_reg = (a_s < b_s) ? {{(WIDTH-1){1'b0}},1'b1} : {WIDTH{1'b0}}; // SLT signed
            4'b1001: res_reg = (a < b) ? {{(WIDTH-1){1'b0}},1'b1} : {WIDTH{1'b0}};     // SLTU unsigned
            4'b1010: res_reg = full_product[WIDTH-1:0]; // MUL (lower WIDTH bits)
            4'b1111: res_reg = a; // PASSA
            default: res_reg = {WIDTH{1'b0}};
        endcase
    end

    assign result    = res_reg;
    assign zero      = (res_reg == {WIDTH{1'b0}});
    assign negative  = res_reg[WIDTH-1];
    assign carry_out = carry_reg;
    assign overflow  = overflow_reg;

endmodule
