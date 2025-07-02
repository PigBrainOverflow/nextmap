module unsigned_extension_test (
    input [3:0] a,
    input [3:0] b,
    output [7:0] out
);
    assign out = a + b;

endmodule