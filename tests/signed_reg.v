module top (
    input clk,
    input [31:0] din,
    output [63:0] dout
);
    // sign-extend din and delay by one cycle
    reg [63:0] dout_reg;
    always @(posedge clk) begin
        dout_reg <= {{32{din[31]}}, din};
    end

    assign dout = dout_reg;
endmodule