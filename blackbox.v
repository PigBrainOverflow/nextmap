module adder_8_bit(
    input [7:0] a,
    input [7:0] b,
    input cin,
    output [7:0] sum,
    output cout
);
    wire cout0;

    adder_4_bit adder0 (
        .a(a[3:0]),
        .b(b[3:0]),
        .cin(cin),
        .sum(sum[3:0]),
        .cout(cout0)
    );

    adder_4_bit adder1 (
        .a(a[7:4]),
        .b(b[7:4]),
        .cin(cout0),
        .sum(sum[7:4]),
        .cout(cout)
    );

endmodule