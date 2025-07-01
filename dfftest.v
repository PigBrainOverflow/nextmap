module dffe_weird (
    input  clk,
    input  d,
    input  en,
    output reg q
);
    always @(posedge clk) begin
        q <= en ? d : q;
    end

endmodule