module top (
    input signed [15:0] a,
    input signed [15:0] b,
    input signed [15:0] c,
    input signed [15:0] d,
    input signed [15:0] e,
    output signed [31:0] y
);
    assign y = a * d + b * d + c * d + e;
endmodule