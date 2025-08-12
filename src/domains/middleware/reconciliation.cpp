#include "crow.h"
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <iomanip>
#include <sstream>

// Function to format a transaction into a fixed-width string for COBOL
std::string format_transaction_for_cobol(const crow::json::rvalue& tx) {
    std::string record;
    record.reserve(190);

    // Helper lambda to safely get string and pad
    auto append_padded = [&](const std::string& key, size_t len) {
        // CORREÇÃO: Usa std::string("") para garantir que ambos os resultados da expressão ternária sejam do tipo std::string,
        // resolvendo o erro de "operand types are incompatible".
        std::string val_str = tx.has(key) ? tx[key].s() : std::string("");
        val_str.resize(len, ' ');
        record += val_str;
    };

    append_padded("id", 36);
    append_padded("date", 10);

    // Amount formatting correction
    double amount = tx.has("amount") ? tx["amount"].d() : 0.0;
    long long amount_in_cents = static_cast<long long>(round(amount * 100));
    std::string amount_str = std::to_string(amount_in_cents);
    if (amount_str.length() > 17) {
        amount_str = amount_str.substr(amount_str.length() - 17);
    }
    std::stringstream ss_amount;
    ss_amount << std::setw(17) << std::setfill('0') << amount_str;
    record += ss_amount.str();

    append_padded("type", 7);
    append_padded("category", 20);
    append_padded("description", 100);

    // Final padding to ensure record is exactly 190 characters
    if (record.length() < 190) {
        record += std::string(190 - record.length(), ' ');
    } else if (record.length() > 190) {
        record = record.substr(0, 190);
    }

    return record;
}


int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/reconcile").methods("POST"_method)
    ([](const crow::request& req) {
        auto request_body = crow::json::load(req.body);
        if (!request_body || !request_body.has("transactions") || request_body["transactions"].t() != crow::json::type::List) {
            return crow::response(400, "Invalid JSON: 'transactions' key with a list is required.");
        }

        const auto& transactions_json = request_body["transactions"];

        std::ofstream input_file("INPUT.DAT");
        if (!input_file.is_open()) {
            return crow::response(500, "Failed to create input file for COBOL process.");
        }
        for (const auto& tx : transactions_json) {
            input_file << format_transaction_for_cobol(tx) << std::endl;
        }
        input_file.close();

        int result = system("./reconcile");
        if (result != 0) {
            remove("INPUT.DAT");
            return crow::response(500, "COBOL process execution failed.");
        }

        std::ifstream summary_file("SUMMARY.DAT");
        if (!summary_file.is_open()) {
            remove("INPUT.DAT");
            return crow::response(500, "Failed to open COBOL summary file.");
        }
        std::string summary_data;
        std::getline(summary_file, summary_data);
        summary_file.close();
        
        if (summary_data.length() < 46) {
             remove("INPUT.DAT");
             remove("SUMMARY.DAT");
             return crow::response(500, "COBOL summary file is malformed or empty.");
        }

        crow::json::wvalue summary_json;
        try {
            summary_json["total_records"] = std::stoll(summary_data.substr(0, 9));
            summary_json["total_debits"] = std::stod(summary_data.substr(9, 17)) / 100.0;
            summary_json["total_credits"] = std::stod(summary_data.substr(26, 17)) / 100.0;
            summary_json["high_value_flag"] = summary_data.substr(43, 1);
            summary_json["duplicate_tx_flag"] = summary_data.substr(44, 1);
            summary_json["data_error_flag"] = summary_data.substr(45, 1);
        } catch (const std::exception& e) {
            remove("INPUT.DAT");
            remove("SUMMARY.DAT");
            return crow::response(500, "Failed to parse COBOL summary data.");
        }

        remove("INPUT.DAT");
        remove("SUMMARY.DAT");

        return crow::response(200, summary_json);
    });

    app.port(18080).multithreaded().run();

    return 0;
}