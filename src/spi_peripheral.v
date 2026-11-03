`default_nettype none

module double_ff_sync (
    input  wire rst_n,
    input  wire clk,
    input  wire d,
    output reg q_b
);

    reg q_a;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin 
            q_a <= 1'b0;
            q_b <= 1'b0;
        end else begin
            q_a <= d;
            q_b <= q_a;
        end
    end
 

endmodule


module spi_peripheral (
    input  wire clk, rst_n,
    input  wire sclk, copi, ncs,
    output reg [7:0] en_reg_out_7_0, en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0, en_reg_pwm_15_8,
    output wire [7:0] pwm_duty_cycle
);

    reg copi_sync;
    reg [15:0] shift_reg;

    reg [3:0] count;

    double_ff_sync double_ff_sync_inst (
        .rst_n(rst_n),
        .clk(clk),
        .d(copi),
        .q_b(copi_sync)
    );

    always @(posedge sclk or negedge ncs) begin
        if (!ncs) begin
            count <= 4'd0;
        end else begin
            shift_reg[count] <= copi_sync;
            count <= count + 1'b1;
        end
    end


endmodule