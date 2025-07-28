#include "crow.h"
#include "gateway.hpp"
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <algorithm>
#include <fstream>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/wait.h>
#include <sys/stat.h>
#endif

bool cobol_executable_exists(const std::string& path) {
#ifdef _WIN32
    DWORD dwAttrib = GetFileAttributesA(path.c_str());
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
#else
    struct stat buffer;
    return (stat(path.c_str(), &buffer) == 0 && (buffer.st_mode & S_IXUSR));
#endif
}

crow::json::wvalue process_without_cobol(const crow::json::rvalue& transactions_json) {
    std::cout << "🔄 Processing transactions without COBOL (fallback mode)" << std::endl;
    
    if (!transactions_json.has("transactions") || transactions_json["transactions"].t() != crow::json::type::List) {
        return crow::json::wvalue{{"error", "Invalid JSON format: 'transactions' array not found."}};
    }

    const auto& transactions = transactions_json["transactions"];
    
    int total_transactions = 0;
    double total_amount = 0.0;
    
    for (const auto& item : transactions) {
        total_transactions++;
        double amount = item.has("amount") ? item["amount"].d() : 0.0;
        total_amount += amount;
        
        std::string category = item.has("category") ? std::string(item["category"].s()) : std::string("unknown");
        std::cout << "  Transaction " << total_transactions 
                  << ": Amount=" << amount 
                  << ", Category=" << category
                  << std::endl;
    }
    
    std::cout << "✅ Processed " << total_transactions << " transactions, total: $" << total_amount << std::endl;
    
    crow::json::wvalue response;
    response["processed_transactions"] = total_transactions;
    response["total_amount"] = total_amount;
    response["processing_mode"] = "fallback_cpp_only";
    response["note"] = "COBOL processor not available, using C++ fallback";
    return response;
}

std::string execute_cobol_process(const std::string& input_data, int& exit_code, std::string& stderr_data) {
    std::string command = "./transaction_processor";
    std::string result_data;
    exit_code = -1;

    if (!cobol_executable_exists(command)) {
        throw std::runtime_error("COBOL executable './transaction_processor' not found or not executable");
    }

    std::cout << "🚀 Executing COBOL process: " << command << std::endl;
    std::cout << "📊 Input data size: " << input_data.length() << " bytes" << std::endl;

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

    if (pid == 0) {
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
        _exit(127);
    } else {
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

    std::cout << "🎯 COBOL process completed with exit code: " << exit_code << std::endl;
    std::cout << "📤 Output size: " << result_data.length() << " bytes" << std::endl;
    if (!stderr_data.empty()) {
        std::cout << "⚠️  Stderr: " << stderr_data << std::endl;
    }

    return result_data;
}

std::vector<unsigned char> to_comp3(long long value, int num_bytes) {
    std::string s_value = std::to_string(std::abs(value));
    if (s_value.length() > (num_bytes * 2) - 1) {
        throw std::runtime_error("Value too large for packed decimal conversion.");
    }
    s_value = std::string((num_bytes * 2) - 1 - s_value.length(), '0') + s_value;

    std::vector<unsigned char> packed(num_bytes);
    for (int i = 0; i < num_bytes - 1; ++i) {
        packed[i] = ((s_value[2 * i] - '0') << 4) | (s_value[2 * i + 1] - '0');
    }

    unsigned char sign = (value < 0) ? 0x0D : 0x0C;
    packed[num_bytes - 1] = ((s_value[(num_bytes * 2) - 2] - '0') << 4) | sign;
    
    return packed;
}

crow::json::wvalue process_transaction_batch(const crow::json::rvalue& transactions_json) {
    std::cout << "🏁 Starting transaction batch processing..." << std::endl;
    
    if (!transactions_json.has("transactions") || transactions_json["transactions"].t() != crow::json::type::List) {
        return crow::json::wvalue{{"error", "Invalid JSON format: 'transactions' array not found."}};
    }

    const auto& transactions = transactions_json["transactions"];
    std::cout << "📊 Processing " << transactions.size() << " transactions" << std::endl;
    
    if (!cobol_executable_exists("./transaction_processor")) {
        std::cout << "⚠️  COBOL executable not found, using fallback processing" << std::endl;
        return process_without_cobol(transactions_json);
    }
    
    std::string input_data_buffer;
    input_data_buffer.reserve(transactions.size() * 59);

    for (size_t i = 0; i < transactions.size(); ++i) {
        const auto& item = transactions[i];
        
        std::cout << "📋 Processing transaction " << (i+1) << "/" << transactions.size() << std::endl;
        
        long long id = item.has("id") ? item["id"].i() : (long long)(i + 1);
        auto packed_id = to_comp3(id, 5);
        input_data_buffer.append(reinterpret_cast<const char*>(packed_id.data()), packed_id.size());

        double amount_value = item.has("amount") ? item["amount"].d() : 0.0;
        long long amount_cents = static_cast<long long>(amount_value * 100);
        auto packed_amount = to_comp3(amount_cents, 8);
        input_data_buffer.append(reinterpret_cast<const char*>(packed_amount.data()), packed_amount.size());

        std::string category = item.has("category") ? std::string(item["category"].s()) : std::string("OTHER");
        category.resize(20, ' ');
        input_data_buffer.append(category);

        std::string timestamp = item.has("transaction_date") ? std::string(item["transaction_date"].s()) : 
                               item.has("date") ? std::string(item["date"].s()) : std::string("1900-01-01");
        timestamp.resize(26, ' ');
        input_data_buffer.append(timestamp);
        
        std::cout << "  ID: " << id << ", Amount: $" << amount_value 
                  << ", Category: " << category.substr(0, 20) 
                  << ", Date: " << timestamp.substr(0, 10) << std::endl;
    }

    int exit_code = 0;
    std::string output_data, stderr_data;
    try {
        output_data = execute_cobol_process(input_data_buffer, exit_code, stderr_data);
    } catch (const std::runtime_error& e) {
        std::cout << "❌ COBOL execution failed: " << e.what() << std::endl;
        std::cout << "🔄 Falling back to C++ processing" << std::endl;
        return process_without_cobol(transactions_json);
    }

    if (exit_code != 0) {
        std::cout << "❌ COBOL process failed with exit code: " << exit_code << std::endl;
        std::cout << "🔄 Falling back to C++ processing" << std::endl;
        return process_without_cobol(transactions_json);
    }

    try {
        if (output_data.length() < 24) {
             throw std::runtime_error("Output from COBOL process is too short. Expected 24 bytes, got " + std::to_string(output_data.length()));
        }

        std::string total_transactions_str = output_data.substr(0, 8);
        std::string total_amount_str = output_data.substr(9, 15);
        
        total_transactions_str.erase(total_transactions_str.find_last_not_of(" \n\r\t")+1);
        total_amount_str.erase(total_amount_str.find_last_not_of(" \n\r\t")+1);

        long long total_transactions = std::stoll(total_transactions_str);
        double total_amount = std::stod(total_amount_str) / 100.0;
        
        std::cout << "✅ COBOL processing successful!" << std::endl;
        std::cout << "📊 Results: " << total_transactions << " transactions, $" << total_amount << std::endl;
        
        crow::json::wvalue response;
        response["processed_transactions"] = total_transactions;
        response["total_amount"] = total_amount;
        response["processing_mode"] = "cobol_legacy";
        return response;
    } catch (const std::exception& e) {
        std::cout << "❌ Failed to parse COBOL output: " << e.what() << std::endl;
        std::cout << "🔄 Falling back to C++ processing" << std::endl;
        return process_without_cobol(transactions_json);
    }
}

int main() {
    crow::SimpleApp app;
    
    std::cout << "🚀 Gateway Server starting on port 8081..." << std::endl;
    std::cout << "🔍 Checking for COBOL executable..." << std::endl;
    
    if (cobol_executable_exists("./transaction_processor")) {
        std::cout << "✅ COBOL executable found and ready" << std::endl;
    } else {
        std::cout << "⚠️  COBOL executable not found - fallback mode will be used" << std::endl;
    }

    CROW_ROUTE(app, "/process").methods("POST"_method)
    ([](const crow::request& req){
        std::cout << "\n🎯 New processing request received" << std::endl;
        std::cout << "📦 Request body size: " << req.body.length() << " bytes" << std::endl;
        
        crow::json::rvalue transactions_json;
        try {
            transactions_json = crow::json::load(req.body);
        } catch (const std::runtime_error& e) {
            std::cout << "❌ JSON parsing failed: " << e.what() << std::endl;
            crow::json::wvalue error_response;
            error_response["error"] = "Invalid JSON.";
            error_response["details"] = e.what();
            return crow::response(400, error_response);
        }

        auto response_data = process_transaction_batch(transactions_json);
        
        if (response_data.count("error")) {
            std::cout << "❌ Processing failed with error" << std::endl;
            return crow::response(500, response_data);
        }

        std::cout << "✅ Processing completed successfully" << std::endl;
        return crow::response(200, response_data);
    });

    CROW_ROUTE(app, "/health").methods("GET"_method)
    ([](){
        crow::json::wvalue health;
        health["status"] = "healthy";
        health["cobol_available"] = cobol_executable_exists("./transaction_processor");
        health["timestamp"] = std::time(nullptr);
        return crow::response(200, health);
    });

    app.port(8081).multithreaded().run();

    return 0;
}