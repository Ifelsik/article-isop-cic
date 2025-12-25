`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 19.12.2025 17:43:52
// Design Name: 
// Module Name: ISOP
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module ISOP (
    input wire clk,
    input wire rst,
    input wire signed [7:0] d_in,    // Вход (от CIC или тестбенча)
    output reg signed [7:0] d_out    // Выход (Скорректированный)
);

    // 1. КОЭФФИЦИЕНТЫ
    // Рассчитаны в Python с BIT_WIDTH = 24.
    // Максимальное значение ~14.9 млн.
    // Для знакового типа нам нужно минимум 25 бит (24 бита значения + знак).
    // Берем [25:0] (26 бит) для надежности.
    localparam signed [25:0] COEFFS [0:14] ='{
         54038,
         -157159,
         477137,
         -1038076,
         1504341,
         -868335, 
         -3125632,
         14901461,
         -3125632,
         -868335,
         1504341,
         -1038076, 
         477137,
         -157159,
         54038
    };

    // 2. ЛИНИЯ ЗАДЕРЖКИ
    integer i;
    reg signed [7:0] shift_reg [0:14];

    // 3. АККУМУЛЯТОР
    // Вход (8) + Коэф (26) + запас на сумму (4) = 38 бит.
    // Берем 40 бит.
    reg signed [39:0] accumulator;
    reg signed [33:0] product; 

    always @(posedge clk) begin
        if (rst) begin
            d_out <= 0;
            accumulator <= 0;
            for (i = 0; i < 15; i = i + 1) shift_reg[i] <= 0;
        end else begin
            // --- Сдвиг данных ---
            shift_reg[0] <= d_in;
            for (i = 1; i < 15; i = i + 1) begin
                shift_reg[i] <= shift_reg[i-1];
            end

            // --- Свертка (FIR Filter) ---
            accumulator = 0;
            for (i = 0; i < 15; i = i + 1) begin
                product = shift_reg[i] * COEFFS[i];
                accumulator = accumulator + product;
            end

            // --- Нормировка выхода (Slicing) ---
            // Масштаб в Python был 2^23 (bit_width=24).
            // Чтобы вернуть амплитуду к 8 битам, делим на 2^23.
            // Берем биты начиная с 23-го: [30:23].
            
            d_out <= accumulator[30:23]; 
        end
    end

endmodule