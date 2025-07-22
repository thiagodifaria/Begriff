#ifndef GATEWAY_HPP
#define GATEWAY_HPP

#include "crow.h"
#include <string>
#include <vector>

// Represents a single transaction
struct Transaction {
    std::string description;
    double amount;
    std::string category;
};

// Processes a batch of transactions from a JSON object
crow::json::wvalue process_transaction_batch(const crow::json::rvalue& transactions_json);

#endif // GATEWAY_HPP
