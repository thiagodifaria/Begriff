#include "crow.h"
#include "gateway.hpp"
#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <cstdlib>
#include <sstream>
#include <iomanip>
#include <cstdio>
#include <random>
#include <algorithm>
#include <iterator>

// Generates a random alphanumeric string of a given length
std::string generate_random_filename(int length) {
    std::string chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    std::random_device rd;
    std::mt19937 generator(rd());
    std::uniform_int_distribution<> distribution(0, chars.size() - 1);
    std::string random_string;
    for (int i = 0; i < length; ++i) {
        random_string += chars[distribution(generator)];
    }
    return random_string;
}

// Packs a long long into a COMP-3 packed decimal format.
// Example: 12345 -> {0x12, 0x34, 0x5C}
std::vector<unsigned char> to_comp3(long long value, int num_bytes) {
    std::vector<unsigned char> packed(num_bytes);
    bool is_negative = value < 0;
    if (is_negative) {
        value = -value;
    }

    for (int i = num_bytes - 1; i >= 0; --i) {
        unsigned char byte = 0;
        if (i == num_bytes - 1) { // Last byte contains the sign
            byte = (value % 10) << 4;
            value /= 10;
            byte |= (is_negative ? 0x0D : 0x0C);
        } else {
            byte = (value % 10) << 4;
            value /= 10;
            byte |= (value % 10);
            value /= 10;
        }
        packed[i] = byte;
    }
    return packed;
}

// Processes a batch of transactions by orchestrating a COBOL program
crow::json::wvalue process_transaction_batch(const crow::json::rvalue& transactions_json) {
    if (!transactions_json.has("transactions") || transactions_json["transactions"].t() != crow::json::type::List) {
        crow::json::wvalue error;
        error["error"] = "Invalid JSON format: 'transactions' array not found.";
        return error;
    }

    const auto& transactions = transactions_json["transactions"];
    
    // Generate unique filenames to prevent race conditions
    std::string input_filename = "input_" + generate_random_filename(12) + ".dat";
    std::string output_filename = "output_" + generate_random_filename(12) + ".dat";

    // 1. Prepare Input File in binary format for COBOL
    std::ofstream input_file(input_filename, std::ios::binary);
    if (!input_file.is_open()) {
        crow::json::wvalue error;
        error["error"] = "Failed to create input file for COBOL process.";
        return error;
    }

    for (const auto& item : transactions) {
        // TR-ID: PIC S9(9) COMP-3 -> 5 bytes
        long long id = item.has("id") ? item["id"].i() : 0;
        auto packed_id = to_comp3(id, 5);
        input_file.write(reinterpret_cast<const char*>(packed_id.data()), packed_id.size());

        // TR-AMOUNT: PIC S9(13)V99 COMP-3 -> 8 bytes
        long long amount_cents = static_cast<long long>((item.has("amount") ? item["amount"].d() : 0.0) * 100);
        auto packed_amount = to_comp3(amount_cents, 8);
        input_file.write(reinterpret_cast<const char*>(packed_amount.data()), packed_amount.size());

        // TR-CATEGORY: PIC X(20)
        std::string category = item.has("category") ? item["category"].s() : "";
        category.resize(20, ' ');
        input_file.write(category.c_str(), 20);

        // TR-TIMESTAMP: PIC X(26)
        std::string timestamp = item.has("transaction_date") ? item["transaction_date"].s() : "";
        timestamp.resize(26, ' ');
        input_file.write(timestamp.c_str(), 26);
    }
    input_file.close();

    // 2. Construct and Execute Command
    std::string command = "./transaction_processor " + input_filename + " " + output_filename;
    int return_code = system(command.c_str());

    if (return_code != 0) {
        crow::json::wvalue error;
        error["error"] = "COBOL process execution failed.";
        error["return_code"] = return_code;
        remove(input_filename.c_str()); // Cleanup
        return error;
    }

    // 3. Parse Output File
    std::ifstream output_file(output_filename);
    if (!output_file.is_open()) {
        crow::json::wvalue error;
        error["error"] = "Failed to open COBOL output file.";
        remove(input_filename.c_str()); // Cleanup
        return error;
    }

    std::string output_line;
    std::getline(output_file, output_line);
    output_file.close();

    crow::json::wvalue response;
    try {
        size_t comma_pos = output_line.find(',');
        if (comma_pos == std::string::npos) {
            throw std::runtime_error("Invalid output format from COBOL process.");
        }
        long long total_transactions = std::stoll(output_line.substr(0, comma_pos));
        double total_amount = std::stod(output_line.substr(comma_pos + 1)) / 100.0;
        
        response["processed_transactions"] = total_transactions;
        response["total_amount"] = total_amount;
    } catch (const std::exception& e) {
        crow::json::wvalue error;
        error["error"] = "Failed to parse COBOL output file.";
        error["details"] = e.what();
        error["raw_output"] = output_line;
        remove(input_filename.c_str());
        remove(output_filename.c_str());
        return error;
    }

    // 4. Cleanup
    remove(input_filename.c_str());
    remove(output_filename.c_str());

    return response;
}

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/process").methods("POST"_method)
    ([](const crow::request& req){
        crow::json::rvalue transactions_json;
        try {
            transactions_json = crow::json::load(req.body);
        } catch (const std::runtime_error& e) {
            crow::json::wvalue error;
            error["error"] = "Invalid JSON.";
            return crow::response(400, error);
        }

        auto response_data = process_transaction_batch(transactions_json);
        
        if (response_data.has("error")) {
            return crow::response(500, response_data);
        }

        return crow::response(200, response_data);
    });

    app.port(8081).multithreaded().run();

    return 0;
}
