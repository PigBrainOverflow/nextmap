module adder64_carry_ahead (
    input  [63:0] a,
    input  [63:0] b,
    input         cin,
    output [63:0] sum,
    output        cout
);
    wire [7:0] G, P;
    wire [7:0] carry;

    assign carry[0] = cin;

    // Compute carries for each 8-bit block
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : block_adders
            adder8_cla adder (
                .a(a[i*8 +: 8]),
                .b(b[i*8 +: 8]),
                .cin(carry[i]),
                .sum(sum[i*8 +: 8]),
                .G(G[i]),
                .P(P[i])
            );

            if (i < 7)
                assign carry[i+1] = G[i] | (P[i] & carry[i]);
        end
    endgenerate

    assign cout = G[7] | (P[7] & carry[7]);
endmodule
