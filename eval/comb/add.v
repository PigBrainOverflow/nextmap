module add (
    input cin,
    input [3:0] a,
    input [3:0] b,
    output cout,
    output [3:0] sum
);
    assign {cout, sum} = a + b + cin;
endmodule