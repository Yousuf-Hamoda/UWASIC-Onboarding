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
    output reg [7:0] pwm_duty_cycle
);

    reg copi_sync;

    double_ff_sync double_ff_sync_inst (
        .rst_n(rst_n),
        .clk(clk),
        .d(copi),
        .q_b(copi_sync)
    );
    

    reg [15:0] shift_reg;
    reg [4:0] count;
    reg sclk_prev;
    
    wire frame_rw = shift_reg[15];
    wire [6:0] frame_addr = shift_reg[14:8];
    wire [7:0] frame_data = shift_reg[7:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sclk_prev <= 1'b0;
            shift_reg <= 16'h0;
            count <= 5'd0;
            en_reg_out_7_0 <= 8'h0;
            en_reg_out_15_8 <= 8'h0;
            en_reg_pwm_7_0 <= 8'h0;
            en_reg_pwm_15_8 <= 8'h0;
            pwm_duty_cycle <= 8'h0;
        end else if (!ncs) begin
            sclk_prev <= sclk; 

            if (sclk && !sclk_prev && count != 5'd16) begin
                shift_reg <= {shift_reg[14:0], copi_sync};
                count <= count + 5'd1;
            end

        end else begin
            if (count == 5'd16 && frame_rw && frame_addr <= 7'h04) begin
                case (frame_addr)
                    7'h00: en_reg_out_7_0 <= frame_data;
                    7'h01: en_reg_out_15_8 <= frame_data;
                    7'h02: en_reg_pwm_7_0 <= frame_data;
                    7'h03: en_reg_pwm_15_8 <= frame_data;
                    7'h04: pwm_duty_cycle <= frame_data;
                    default: ;
                endcase
            end 
            count <= 5'd0;
        end
    end

endmodule