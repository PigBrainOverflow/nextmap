module top (
    input clk,
    input [7:0] raddr,
    input [7:0] waddr,
    input [7:0] wdata,
    input we,
    output [7:0] rdata
);

    reg [7:0] mem [255:0];
    reg [7:0] rdata_reg;

    always @(posedge clk) begin
        if (we) begin
            mem[waddr] <= wdata;
        end
        // synchronous read
        rdata_reg <= mem[raddr];
    end

    assign rdata = rdata_reg;

endmodule