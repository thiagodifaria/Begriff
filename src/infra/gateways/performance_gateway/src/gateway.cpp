#include "crow.h"
#include "gateway.hpp"

#include <algorithm>
#include <cmath>
#include <cctype>
#include <ctime>
#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace {
constexpr const char* kCobolExecutable = "./transaction_processor";
constexpr long long kMaxTransactionId = 999999999LL;
constexpr double kMaxAbsoluteAmount = 100000000000.0;
const std::regex kDateRegex("^\\d{4}-\\d{2}-\\d{2}([T\\s].*)?$");

std::string trim(const std::string& value) {
    const auto start = value.find_first_not_of(" \n\r\t");
    if (start == std::string::npos) {
        return "";
    }
    const auto end = value.find_last_not_of(" \n\r\t");
    return value.substr(start, end - start + 1);
}

bool is_safe_text(const std::string& value, size_t max_len) {
    if (value.empty() || value.size() > max_len) {
        return false;
    }
    for (char c : value) {
        if (!(std::isalnum(static_cast<unsigned char>(c)) || c == '_' || c == '-' || c == ' ' || c == '/')) {
            return false;
        }
    }
    return true;
}

bool parse_amount(const crow::json::rvalue& item, double& amount_out) {
    if (!item.has("amount")) {
        amount_out = 0.0;
        return true;
    }
    if (item["amount"].t() == crow::json::type::Number) {
        amount_out = item["amount"].d();
        return std::isfinite(amount_out);
    }
    if (item["amount"].t() == crow::json::type::String) {
        try {
            amount_out = std::stod(std::string(item["amount"].s()));
            return std::isfinite(amount_out);
        } catch (...) {
            return false;
        }
    }
    return false;
}

bool parse_id(const crow::json::rvalue& item, long long fallback, long long& id_out) {
    if (!item.has("id")) {
        id_out = fallback;
        return true;
    }
    if (item["id"].t() == crow::json::type::Number) {
        id_out = item["id"].i();
        return true;
    }
    if (item["id"].t() == crow::json::type::String) {
        try {
            id_out = std::stoll(std::string(item["id"].s()));
            return true;
        } catch (...) {
            return false;
        }
    }
    return false;
}

bool cobol_executable_exists(const std::string& path) {
#ifdef _WIN32
    DWORD dwAttrib = GetFileAttributesA(path.c_str());
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
#else
    struct stat buffer {};
    return (stat(path.c_str(), &buffer) == 0 && (buffer.st_mode & S_IXUSR));
#endif
}

std::vector<unsigned char> to_comp3(long long value, int num_bytes) {
    std::string s_value = std::to_string(std::abs(value));
    if (s_value.length() > static_cast<size_t>((num_bytes * 2) - 1)) {
        throw std::runtime_error("Value too large for packed decimal conversion");
    }
    s_value = std::string((num_bytes * 2) - 1 - s_value.length(), '0') + s_value;

    std::vector<unsigned char> packed(num_bytes);
    for (int i = 0; i < num_bytes - 1; ++i) {
        packed[i] = ((s_value[2 * i] - '0') << 4) | (s_value[2 * i + 1] - '0');
    }

    const unsigned char sign = (value < 0) ? 0x0D : 0x0C;
    packed[num_bytes - 1] = ((s_value[(num_bytes * 2) - 2] - '0') << 4) | sign;
    return packed;
}

std::string execute_cobol_process(const std::string& input_data, int& exit_code, std::string& stderr_data) {
    std::string command = kCobolExecutable;
    std::string result_data;
    exit_code = -1;

    if (!cobol_executable_exists(command)) {
        throw std::runtime_error("COBOL executable not found");
    }

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

    if (!CreatePipe(&hChildStd_OUT_Rd, &hChildStd_OUT_Wr, &saAttr, 0)) {
        throw std::runtime_error("Stdout pipe creation failed");
    }
    if (!SetHandleInformation(hChildStd_OUT_Rd, HANDLE_FLAG_INHERIT, 0)) {
        throw std::runtime_error("Stdout pipe handle inheritance failed");
    }

    if (!CreatePipe(&hChildStd_ERR_Rd, &hChildStd_ERR_Wr, &saAttr, 0)) {
        throw std::runtime_error("Stderr pipe creation failed");
    }
    if (!SetHandleInformation(hChildStd_ERR_Rd, HANDLE_FLAG_INHERIT, 0)) {
        throw std::runtime_error("Stderr pipe handle inheritance failed");
    }

    if (!CreatePipe(&hChildStd_IN_Rd, &hChildStd_IN_Wr, &saAttr, 0)) {
        throw std::runtime_error("Stdin pipe creation failed");
    }
    if (!SetHandleInformation(hChildStd_IN_Wr, HANDLE_FLAG_INHERIT, 0)) {
        throw std::runtime_error("Stdin pipe handle inheritance failed");
    }

    PROCESS_INFORMATION piProcInfo = {0};
    STARTUPINFOA siStartInfo = {0};
    siStartInfo.cb = sizeof(STARTUPINFO);
    siStartInfo.hStdError = hChildStd_ERR_Wr;
    siStartInfo.hStdOutput = hChildStd_OUT_Wr;
    siStartInfo.hStdInput = hChildStd_IN_Rd;
    siStartInfo.dwFlags |= STARTF_USESTDHANDLES;

    if (!CreateProcessA(NULL, (LPSTR)command.c_str(), NULL, NULL, TRUE, 0, NULL, NULL, &siStartInfo, &piProcInfo)) {
        throw std::runtime_error("CreateProcess failed");
    }

    CloseHandle(hChildStd_OUT_Wr);
    CloseHandle(hChildStd_ERR_Wr);
    CloseHandle(hChildStd_IN_Rd);

    DWORD dwWritten;
    WriteFile(hChildStd_IN_Wr, input_data.c_str(), static_cast<DWORD>(input_data.length()), &dwWritten, NULL);
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
    DWORD proc_exit_code = 0;
    GetExitCodeProcess(piProcInfo.hProcess, &proc_exit_code);
    exit_code = static_cast<int>(proc_exit_code);
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
        _exit(127);
    }

    close(stdin_pipe[0]);
    write(stdin_pipe[1], input_data.c_str(), input_data.length());
    close(stdin_pipe[1]);

    close(stdout_pipe[1]);
    char buffer[4096];
    ssize_t count = 0;
    while ((count = read(stdout_pipe[0], buffer, sizeof(buffer))) > 0) {
        result_data.append(buffer, count);
    }
    close(stdout_pipe[0]);

    close(stderr_pipe[1]);
    while ((count = read(stderr_pipe[0], buffer, sizeof(buffer))) > 0) {
        stderr_data.append(buffer, count);
    }
    close(stderr_pipe[0]);

    int status = 0;
    waitpid(pid, &status, 0);
    if (WIFEXITED(status)) {
        exit_code = WEXITSTATUS(status);
    }
#endif

    return result_data;
}

crow::json::wvalue process_without_cobol(const crow::json::rvalue& transactions_json) {
    crow::json::wvalue response;
    if (!transactions_json.has("transactions") || transactions_json["transactions"].t() != crow::json::type::List) {
        response["error"] = "Invalid JSON format: 'transactions' array not found";
        return response;
    }

    const auto& transactions = transactions_json["transactions"];
    int total_transactions = 0;
    double total_amount = 0.0;

    for (const auto& item : transactions) {
        double amount = 0.0;
        if (!parse_amount(item, amount)) {
            continue;
        }
        total_transactions++;
        total_amount += amount;
    }

    response["processed_transactions"] = total_transactions;
    response["total_amount"] = total_amount;
    response["processing_mode"] = "fallback_cpp_only";
    return response;
}
}  // namespace

crow::json::wvalue process_transaction_batch(const crow::json::rvalue& transactions_json) {
    crow::json::wvalue error_response;
    if (!transactions_json.has("transactions") || transactions_json["transactions"].t() != crow::json::type::List) {
        error_response["error"] = "Invalid JSON format: 'transactions' array not found";
        return error_response;
    }

    const auto& transactions = transactions_json["transactions"];
    if (transactions.empty()) {
        error_response["error"] = "At least one transaction is required";
        return error_response;
    }

    if (!cobol_executable_exists(kCobolExecutable)) {
        return process_without_cobol(transactions_json);
    }

    std::string input_data_buffer;
    input_data_buffer.reserve(transactions.size() * 59);
    int invalid_transactions = 0;

    for (size_t i = 0; i < transactions.size(); ++i) {
        const auto& item = transactions[i];
        long long id = 0;
        double amount_value = 0.0;

        if (!parse_id(item, static_cast<long long>(i + 1), id) || id <= 0 || id > kMaxTransactionId) {
            invalid_transactions++;
            continue;
        }
        if (!parse_amount(item, amount_value) || std::abs(amount_value) > kMaxAbsoluteAmount) {
            invalid_transactions++;
            continue;
        }

        std::string category = item.has("category") ? std::string(item["category"].s()) : "OTHER";
        if (!is_safe_text(category, 20)) {
            invalid_transactions++;
            continue;
        }

        std::string timestamp = item.has("transaction_date")
                                    ? std::string(item["transaction_date"].s())
                                    : (item.has("date") ? std::string(item["date"].s()) : "1900-01-01");
        if (!std::regex_match(timestamp, kDateRegex)) {
            invalid_transactions++;
            continue;
        }

        const auto packed_id = to_comp3(id, 5);
        input_data_buffer.append(reinterpret_cast<const char*>(packed_id.data()), packed_id.size());

        const auto amount_cents = static_cast<long long>(std::llround(amount_value * 100.0));
        const auto packed_amount = to_comp3(amount_cents, 8);
        input_data_buffer.append(reinterpret_cast<const char*>(packed_amount.data()), packed_amount.size());

        category.resize(20, ' ');
        input_data_buffer.append(category);

        timestamp.resize(26, ' ');
        input_data_buffer.append(timestamp);
    }

    if (input_data_buffer.empty()) {
        error_response["error"] = "No valid transactions to process";
        error_response["invalid_transactions"] = invalid_transactions;
        return error_response;
    }

    int exit_code = 0;
    std::string output_data;
    std::string stderr_data;
    try {
        output_data = execute_cobol_process(input_data_buffer, exit_code, stderr_data);
    } catch (const std::exception&) {
        return process_without_cobol(transactions_json);
    }

    if (exit_code != 0) {
        return process_without_cobol(transactions_json);
    }

    try {
        if (output_data.length() < 24) {
            throw std::runtime_error("Output too short");
        }

        std::string total_transactions_str = trim(output_data.substr(0, 8));
        std::string total_amount_str = trim(output_data.substr(9, 15));
        if (total_transactions_str.empty() || total_amount_str.empty()) {
            throw std::runtime_error("Invalid output");
        }

        const long long total_transactions = std::stoll(total_transactions_str);
        const double total_amount = std::stod(total_amount_str) / 100.0;

        crow::json::wvalue response;
        response["processed_transactions"] = total_transactions;
        response["total_amount"] = total_amount;
        response["invalid_transactions"] = invalid_transactions;
        response["processing_mode"] = "cobol_legacy";
        return response;
    } catch (const std::exception&) {
        return process_without_cobol(transactions_json);
    }
}

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/process").methods("POST"_method)([](const crow::request& req) {
        crow::json::rvalue transactions_json;
        try {
            transactions_json = crow::json::load(req.body);
        } catch (const std::runtime_error& e) {
            crow::json::wvalue error_response;
            error_response["error"] = "Invalid JSON";
            error_response["details"] = e.what();
            return crow::response(400, error_response);
        }

        auto response_data = process_transaction_batch(transactions_json);
        if (response_data.count("error")) {
            return crow::response(400, response_data);
        }
        return crow::response(200, response_data);
    });

    CROW_ROUTE(app, "/health").methods("GET"_method)([] {
        crow::json::wvalue health;
        health["status"] = "healthy";
        health["cobol_available"] = cobol_executable_exists(kCobolExecutable);
        health["timestamp"] = static_cast<int64_t>(std::time(nullptr));
        return crow::response(200, health);
    });

    app.port(8081).multithreaded().run();
    return 0;
}
