/* Generated Module */
module multiplier (
    input [7:0] a,
    input [7:0] b,
    output [15:0] result
);

    // wire declarations
    wire [15:0] wire_0;

    assign wire_0 = a * b;
    assign result = wire_0;

endmodule
