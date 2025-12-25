`timescale 1ns/1ps

module tb_ISOP;

    // --- 1. Сигналы и переменные ---
    logic clk;
    logic rst;
    logic signed [7:0] d_in;
    logic signed [7:0] d_out;

    // Переменные для работы с файлами
    int file_in, file_out, status;
    
    // Пути к файлам (ЗАМЕНИ НА СВОИ!)
    // В Windows пути лучше писать через слеши / или двойные бэкслеши \\
    string input_file_path = "C:/Users/misha/plis/isop/data/isop_input_chirp.txt"; 
    string output_file_path = "C:/Users/misha/plis/isop/data/output.txt";

    // --- 2. Подключение тестируемого модуля (DUT) ---
    ISOP dut (
        .clk(clk),
        .rst(rst),
        .d_in(d_in),
        .d_out(d_out)
    );

    // --- 3. Генерация клока (100 МГц) ---
    initial clk = 0;
    always #5 clk = ~clk;

    // --- 4. Основной процесс ---
    initial begin
        // Инициализация
        rst = 1;
        d_in = 0;

        // Открытие файлов
        file_in = $fopen(input_file_path, "r");
        file_out = $fopen(output_file_path, "w");

        if (file_in == 0) begin
            $display("ERROR: Не удалось открыть входной файл: %s", input_file_path);
            $stop;
        end

        // Сброс (Reset)
        #20;
        @(posedge clk);
        rst = 0;
        $display("Симуляция начата...");

        // --- Цикл чтения и обработки ---
        while (!$feof(file_in)) begin
            @(posedge clk); // Ждем фронта клока
            
            // Читаем число из файла в d_in
            status = $fscanf(file_in, "%d\n", d_in);
            
            // Сразу пишем текущий выход в файл. 
            // (Учти: d_out отстает от d_in на ~15 тактов, в начале будут нули)
            $fwrite(file_out, "%d\n", d_out);
        end

        // --- Очистка конвейера (Pipeline Flush) ---
        // Так как фильтр имеет задержку (Shift Register), последние данные еще внутри.
        // Нужно подать нули и подождать, пока всё выйдет наружу.
        $display("Flushing pipeline...");
        repeat(20) begin
            @(posedge clk);
            d_in = 0; // Подаем тишину
            $fwrite(file_out, "%d\n", d_out);
        end

        // --- Завершение ---
        $fclose(file_in);
        $fclose(file_out);
        $display("Симуляция завершена, результат записан: %s", output_file_path);
        $stop;
    end

endmodule