#include "crow.h"
#include "gateway.hpp"
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <algorithm>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/wait.h>
#endif

// A robust, cross-platform function to execute the COBOL process,
// piping data to its stdin and reading from its stdout and stderr.
std::string execute_cobol_process(const std::string& input_data, int& exit_code, std::string& stderr_data) {
    std::string command = "./transaction_processor"; // More explicit path
    std::string result_data;
    exit_code = -1;

#ifdef _WIN32
    HANDLE hChildStd_IN_Rd = NULL;
    HANDLE hChildStd_IN_Wr = NULL;
    HANDLE hChildStd_OUT_Rd = NULL;
    HANDLE hChildStd_OUT_Wr = NULL;
    HANDLE hChildStd_ERR_Rd = NULL;
    HANDLE hChildStd_ERR_Wr = NULL;

    SECURITY_ATTRIBUTES saAttr;
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    if (!CreatePipe(&hChildStd_OUT_Rd, &hChildStd_OUT_Wr, &saAttr, 0))
        throw std::runtime_error("Stdout pipe creation failed");
    if (!SetHandleInformation(hChildStd_OUT_Rd, HANDLE_FLAG_INHERIT, 0))
        throw std::runtime_error("Stdout pipe handle inheritance failed");

    if (!CreatePipe(&hChildStd_ERR_Rd, &hChildStd_ERR_Wr, &saAttr, 0))
        throw std::runtime_error("Stderr pipe creation failed");
    if (!SetHandleInformation(hChildStd_ERR_Rd, HANDLE_FLAG_INHERIT, 0))
        throw std::runtime_error("Stderr pipe handle inheritance failed");

    if (!CreatePipe(&hChildStd_IN_Rd, &hChildStd_IN_Wr, &saAttr, 0))
        throw std::runtime_error("Stdin pipe creation failed");
    if (!SetHandleInformation(hChildStd_IN_Wr, HANDLE_FLAG_INHERIT, 0))
        throw std::runtime_error("Stdin pipe handle inheritance failed");

    PROCESS_INFORMATION piProcInfo = {0};
    STARTUPINFOA siStartInfo = {0};
    siStartInfo.cb = sizeof(STARTUPINFO);
    siStartInfo.hStdError = hChildStd_ERR_Wr;
    siStartInfo.hStdOutput = hChildStd_OUT_Wr;
    siStartInfo.hStdInput = hChildStd_IN_Rd;
    siStartInfo.dwFlags |= STARTF_USESTDHANDLES;

    if (!CreateProcessA(NULL, (LPSTR)command.c_str(), NULL, NULL, TRUE, 0, NULL, NULL, &siStartInfo, &piProcInfo))
        throw std::runtime_error("CreateProcess failed");

    CloseHandle(hChildStd_OUT_Wr);
    CloseHandle(hChildStd_ERR_Wr);
    CloseHandle(hChildStd_IN_Rd);

    DWORD dwWritten;
    if (!WriteFile(hChildStd_IN_Wr, input_data.c_str(), (DWORD)input_data.length(), &dwWritten, NULL)) {
        // Writing to a closed pipe may fail, which is okay if the child process exited early.
    }
    CloseHandle(hChildStd_IN_Wr);

    DWORD dwRead;
    CHAR chBuf[4096];
    while (ReadFile(hChildStd_OUT_Rd, chBuf, sizeof(chBuf), &dwRead, NULL) && dwRead != 0) {
        result_data.append(chBuf, dwRead);
    }
    CloseHandle(hChildStd_OUT_Rd);

    while (ReadFile(hChildStd_ERR_Rd, chBuf, sizeof(chBuf), &dwRead, NULL) && dwRead != 0) {
        stderr_data.append(chBuf, dwRead);
    }
    CloseHandle(hChildStd_ERR_Rd);

    WaitForSingleObject(piProcInfo.hProcess, INFINITE);
    DWORD proc_exit_code;
    GetExitCodeProcess(piProcInfo.hProcess, &proc_exit_code);
    exit_code = proc_exit_code;

    CloseHandle(piProcInfo.hProcess);
    CloseHandle(piProcInfo.hThread);
#else
    int stdin_pipe[2];
    int stdout_pipe[2];
    int stderr_pipe[2];
    if (pipe(stdin_pipe) < 0 || pipe(stdout_pipe) < 0 || pipe(stderr_pipe) < 0) {
        throw std::runtime_error("Pipe creation failed");
    }

    pid_t pid = fork();
    if (pid < 0) {
        throw std::runtime_error("Fork failed");
    }

    if (pid == 0) { // Child process
        close(stdin_pipe[1]);
        dup2(stdin_pipe[0], STDIN_FILENO);
        close(stdin_pipe[0]);

        close(stdout_pipe[0]);
        dup2(stdout_pipe[1], STDOUT_FILENO);
        close(stdout_pipe[1]);

        close(stderr_pipe[0]);
        dup2(stderr_pipe[1], STDERR_FILENO);
        close(stderr_pipe[1]);

        execlp(command.c_str(), command.c_str(), NULL);
        perror("execlp");
        _exit(127); // If execlp fails
    } else { // Parent process
        close(stdin_pipe[0]);
        write(stdin_pipe[1], input_data.c_str(), input_data.length());
        close(stdin_pipe[1]);

        close(stdout_pipe[1]);
        char buffer[4096];
        ssize_t count;
        while ((count = read(stdout_pipe[0], buffer, sizeof(buffer))) > 0) {
            result_data.append(buffer, count);
        }
        close(stdout_pipe[0]);

        close(stderr_pipe[1]);
        while ((count = read(stderr_pipe[0], buffer, sizeof(buffer))) > 0) {
            stderr_data.append(buffer, count);
        }
        close(stderr_pipe[0]);

        int status;
        waitpid(pid, &status, 0);
        if (WIFEXITED(status)) {
            exit_code = WEXITSTATUS(status);
        }
    }
#endif
    return result_data;
}

// Packs a long long into a COMP-3 packed decimal format.
std::vector<unsigned char> to_comp3(long long value, int num_bytes) {
    std::string s_value = std::to_string(std::abs(value));
    int num_digits = (num_bytes * 2) - 1;
    s_value = std::string(num_digits - s_value.length(), '0') + s_value;

    std::vector<unsigned char> packed(num_bytes);
    for (int i = 0; i < num_bytes - 1; ++i) {
        packed[i] = ((s_value[2 * i] - '0') << 4) | (s_value[2 * i + 1] - '0');
    }

    unsigned char sign = (value < 0) ? 0x0D : 0x0C;
    packed[num_bytes - 1] = ((s_value[num_digits - 1] - '0') << 4) | sign;
    
    return packed;
}

// Processes a batch of transactions by orchestrating a COBOL program
crow::json::wvalue process_transaction_batch(const crow::json::rvalue& transactions_json) {
    if (!transactions_json.has("transactions") || transactions_json["transactions"].t() != crow::json::type::List) {
        return crow::json::wvalue{{"error", "Invalid JSON format: 'transactions' array not found."}};
    }

    const auto& transactions = transactions_json["transactions"];
    
    std::string input_data_buffer;
    input_data_buffer.reserve(transactions.size() * 59);

    for (const auto& item : transactions) {
        long long id = item.has("id") ? item["id"].i() : 0;
        auto packed_id = to_comp3(id, 5);
        input_data_buffer.append(reinterpret_cast<const char*>(packed_id.data()), packed_id.size());

        long long amount_cents = static_cast<long long>((item.has("amount") ? item["amount"].d() : 0.0) * 100);
        auto packed_amount = to_comp3(amount_cents, 8);
        input_data_buffer.append(reinterpret_cast<const char*>(packed_amount.data()), packed_amount.size());

        std::string category = item.has("category") ? item["category"].s() : "";
        category.resize(20, ' ');
        input_data_buffer.append(category);

        std::string timestamp = item.has("transaction_date") ? item["transaction_date"].s() : "";
        timestamp.resize(26, ' ');
        input_data_buffer.append(timestamp);
    }

    int exit_code = 0;
    std::string output_data, stderr_data;
    try {
        output_data = execute_cobol_process(input_data_buffer, exit_code, stderr_data);
    } catch (const std::runtime_error& e) {
        return crow::json::wvalue{
            {"error", "Failed to execute COBOL process."},
            {"details", e.what()}
        };
    }

    if (exit_code != 0) {
        return crow::json::wvalue{
            {"error", "COBOL process execution failed."},
            {"return_code", exit_code},
            {"stderr", stderr_data},
            {"stdout", output_data}
        };
    }

    try {
        // The COBOL output is a fixed-width record.
        // RP-TOTAL-TRANSACTIONS: PIC 9(8) -> 8 bytes
        // FILLER: PIC X(1) -> 1 byte
        // RP-TOTAL-AMOUNT: PIC S9(13)V99 -> 15 bytes (1 sign + 15 digits)
        if (output_data.length() < 24) { // 8 + 1 + 15
             throw std::runtime_error("Output from COBOL process is too short. Expected 24 bytes.");
        }

        std::string total_transactions_str = output_data.substr(0, 8);
        std::string total_amount_str = output_data.substr(9, 15);
        
        // Trim whitespace
        total_transactions_str.erase(total_transactions_str.find_last_not_of(" \n\r\t")+1);
        total_amount_str.erase(total_amount_str.find_last_not_of(" \n\r\t")+1);

        long long total_transactions = std::stoll(total_transactions_str);
        double total_amount = std::stod(total_amount_str) / 100.0;
        
        crow::json::wvalue response;
        response["processed_transactions"] = total_transactions;
        response["total_amount"] = total_amount;
        return response;
    } catch (const std::exception& e) {
        return crow::json::wvalue{
            {"error", "Failed to parse COBOL output."},
            {"details", e.what()},
            {"raw_output", output_data}
        };
    }
}

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/process").methods("POST"_method)
    ([](const crow::request& req){
        crow::json::rvalue transactions_json;
        try {
            transactions_json = crow::json::load(req.body);
        } catch (const std::runtime_error& e) {
            return crow::response(400, crow::json::wvalue{{"error", "Invalid JSON."}});
        }

        auto response_data = process_transaction_batch(transactions_json);
        
        if (response_data.count("error")) {
            return crow::response(500, response_data);
        }

        return crow::response(200, response_data);
    });

    app.port(8081).multithreaded().run();

    return 0;
}
