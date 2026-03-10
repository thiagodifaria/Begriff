#include "crow.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <regex>
#include <sstream>
#include <string>

namespace {
const std::regex kDateRegex("^\\d{4}-\\d{2}-\\d{2}$");
const std::regex kSafeTextRegex("^[A-Za-z0-9 _\\-/]{1,100}$");

bool is_safe_text(const std::string& value, size_t max_len) {
    return !value.empty() && value.size() <= max_len && std::regex_match(value, kSafeTextRegex);
}

bool is_valid_tx(const crow::json::rvalue& tx) {
    if (!tx.has("id") || !tx.has("date") || !tx.has("amount") || !tx.has("type")) {
        return false;
    }

    const std::string id = tx["id"].s();
    const std::string date = tx["date"].s();
    const std::string type = tx["type"].s();
    const std::string category = tx.has("category") ? std::string(tx["category"].s()) : "UNCATEGORIZED";
    const std::string description = tx.has("description") ? std::string(tx["description"].s()) : "NO_DESCRIPTION";

    if (!is_safe_text(id, 36) || !std::regex_match(date, kDateRegex)) {
        return false;
    }
    if (type != "DEBIT" && type != "CREDIT") {
        return false;
    }
    if (!is_safe_text(category, 20) || !is_safe_text(description, 100)) {
        return false;
    }
    return tx["amount"].t() == crow::json::type::Number;
}

std::string format_transaction_for_cobol(const crow::json::rvalue& tx) {
    std::string record;
    record.reserve(190);

    auto append_padded = [&](const std::string& value, size_t len) {
        std::string val_str = value;
        val_str.resize(len, ' ');
        record += val_str;
    };

    const std::string id = tx["id"].s();
    const std::string date = tx["date"].s();
    const std::string type = tx["type"].s();
    const std::string category = tx.has("category") ? std::string(tx["category"].s()) : "UNCATEGORIZED";
    const std::string description = tx.has("description") ? std::string(tx["description"].s()) : "NO_DESCRIPTION";

    append_padded(id, 36);
    append_padded(date, 10);

    const double amount = tx["amount"].d();
    const auto amount_in_cents = static_cast<long long>(std::llround(amount * 100.0));
    std::stringstream ss_amount;
    ss_amount << std::setw(17) << std::setfill('0') << amount_in_cents;
    record += ss_amount.str();

    append_padded(type, 7);
    append_padded(category, 20);
    append_padded(description, 100);
    return record;
}
}  // namespace

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/reconcile").methods("POST"_method)([](const crow::request& req) {
        auto request_body = crow::json::load(req.body);
        if (!request_body || !request_body.has("transactions") ||
            request_body["transactions"].t() != crow::json::type::List) {
            return crow::response(400, "Invalid JSON: 'transactions' key with a list is required");
        }

        const auto& transactions_json = request_body["transactions"];
        std::ofstream input_file("INPUT.DAT");
        if (!input_file.is_open()) {
            return crow::response(500, "Failed to create input file for COBOL process");
        }

        int invalid_count = 0;
        for (const auto& tx : transactions_json) {
            if (!is_valid_tx(tx)) {
                invalid_count++;
                continue;
            }
            input_file << format_transaction_for_cobol(tx) << std::endl;
        }
        input_file.close();

        if (invalid_count == static_cast<int>(transactions_json.size())) {
            std::remove("INPUT.DAT");
            return crow::response(400, "All transactions were invalid");
        }

        const int result = std::system("./reconcile");
        if (result != 0) {
            std::remove("INPUT.DAT");
            return crow::response(500, "COBOL process execution failed");
        }

        std::ifstream summary_file("SUMMARY.DAT");
        if (!summary_file.is_open()) {
            std::remove("INPUT.DAT");
            return crow::response(500, "Failed to open COBOL summary file");
        }

        std::string summary_data;
        std::getline(summary_file, summary_data);
        summary_file.close();

        if (summary_data.length() < 46) {
            std::remove("INPUT.DAT");
            std::remove("SUMMARY.DAT");
            return crow::response(500, "COBOL summary file is malformed or empty");
        }

        crow::json::wvalue summary_json;
        try {
            summary_json["total_records"] = std::stoll(summary_data.substr(0, 9));
            summary_json["total_debits"] = std::stod(summary_data.substr(9, 17)) / 100.0;
            summary_json["total_credits"] = std::stod(summary_data.substr(26, 17)) / 100.0;
            summary_json["high_value_flag"] = summary_data.substr(43, 1);
            summary_json["duplicate_tx_flag"] = summary_data.substr(44, 1);
            summary_json["data_error_flag"] = summary_data.substr(45, 1);
            summary_json["invalid_input_records"] = invalid_count;
        } catch (const std::exception&) {
            std::remove("INPUT.DAT");
            std::remove("SUMMARY.DAT");
            return crow::response(500, "Failed to parse COBOL summary data");
        }

        std::remove("INPUT.DAT");
        std::remove("SUMMARY.DAT");
        return crow::response(200, summary_json);
    });

    app.port(18080).multithreaded().run();
    return 0;
}
