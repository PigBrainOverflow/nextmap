module top (
    input signed [15:0] a,
    input signed [15:0] b,
    input signed [15:0] c,
    output signed [31:0] y
);
    assign y = a * b + a * c;
endmodule