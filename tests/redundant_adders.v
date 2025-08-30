module top (
    input [31:0] a,
    input [31:0] b,
    output [31:0] y1,
    output [15:0] y2,
    output [7:0] y3
);
    assign y1 = a + b;
    assign y2 = a[15:0] + b[15:0];
    assign y3 = a[7:0] + b[7:0];
endmodule

// module top (
//     input [31:0] a,
//     input [31:0] b,
//     output [31:0] y1
// );
//     assign y1 = a + b;
// endmodule