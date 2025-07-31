module top (
    input clk,
    input [0:0] a,
    input [0:0] b,
    output [1:0] out
);
    // pipeline depth = 2
    // need to retime the multiplication
    reg [1:0] out_reg;

    always @(posedge clk) begin
        out_reg <= a * b;  // Retiming the multiplication
    end

    assign out = out_reg;  // Output the result from the register
endmodule