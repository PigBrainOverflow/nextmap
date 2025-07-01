module adder16_carry_ahead (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout
);
    wire G0, P0, G1, P1;
    wire c1;

    // Lower 8 bits
    adder8_cla adder_low (
        .a   (a[7:0]),
        .b   (b[7:0]),
        .cin (cin),
        .sum (sum[7:0]),
        .G   (G0),
        .P   (P0)
    );

    // Carry to upper block
    assign c1 = G0 | (P0 & cin);

    // Upper 8 bits
    adder8_cla adder_high (
        .a   (a[15:8]),
        .b   (b[15:8]),
        .cin (c1),
        .sum (sum[15:8]),
        .G   (G1),
        .P   (P1)
    );

    // Final carry-out
    assign cout = G1 | (P1 & c1);
endmodule
