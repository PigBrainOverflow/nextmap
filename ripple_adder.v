module top (
    input clk,
    input [3:0] a,
    input [3:0] b,
    output [4:0] sum
);
    // by logic gates
    wire [3:0] carry;
    assign sum[0] = a[0] ^ b[0];
    assign carry[0] = a[0] & b[0];
    assign sum[1] = a[1] ^ b[1] ^ carry[0];
    assign carry[1] = (a[1] & b[1]) | (carry[0] & (a[1] ^ b[1]));
    assign sum[2] = a[2] ^ b[2] ^ carry[1];
    assign carry[2] = (a[2] & b[2]) | (carry[1] & (a[2] ^ b[2]));
    assign sum[3] = a[3] ^ b[3] ^ carry[2];
    assign carry[3] = (a[3] & b[3]) | (carry[2] & (a[3] ^ b[3]));
    assign sum[0] = sum[0];
    assign sum[1] = sum[1];
    assign sum[2] = sum[2];
    assign sum[3] = sum[3];
    assign sum[4] = carry[3];
endmodule