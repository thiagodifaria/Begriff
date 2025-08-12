#include "crow.h"
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <openssl/sha.h>
#include <iomanip>
#include <sstream>

// This is a mock function. In a real scenario, you would use a C++ Web3 library.
std::string commit_to_blockchain(const std::string& data_hash) {
    std::cout << "Connecting to blockchain node..." << std::endl;
    std::cout << "Loading contract ABI and address..." << std::endl;
    std::cout << "Building transaction with hash: " << data_hash << std::endl;
    std::cout << "Signing transaction with secure private key..." << std::endl;
    std::cout << "Sending transaction to the network..." << std::endl;
    
    // Simulate a transaction hash (using the first 64 chars of the data hash for consistency)
    return "0x" + data_hash.substr(0, 64);
}

// Function to recursively sort JSON keys for canonical representation
void sort_json_keys(crow::json::wvalue& j) {
    if (j.t() != crow::json::type::Object) {
        return;
    }

    // CORREÇÃO: Utiliza o método .keys() da biblioteca Crow para obter as chaves.
    // A iteração direta sobre 'j' não é suportada e causava o erro de compilação.
    std::vector<std::string> keys = j.keys();
    std::sort(keys.begin(), keys.end());

    crow::json::wvalue sorted_j;
    for (const auto& key : keys) {
        // Recursively sort child objects
        sort_json_keys(j[key]);
        sorted_j[key] = std::move(j[key]);
    }
    j = std::move(sorted_j);
}

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/secure-commit").methods("POST"_method)
    ([](const crow::request& req) {
        auto report_json = crow::json::load(req.body);

        // 1. Canonicalize JSON to string
        crow::json::wvalue w_report(report_json); // Create a writable copy
        sort_json_keys(w_report);
        std::string canonical_string = w_report.dump(); // Use the .dump() member function

        // 2. Hash the canonical string using SHA-256
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256_CTX sha256;
        SHA256_Init(&sha256);
        SHA256_Update(&sha256, canonical_string.c_str(), canonical_string.size());
        SHA256_Final(hash, &sha256);

        std::stringstream ss;
        for(int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
            ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
        }
        std::string data_hash = ss.str();

        // 3. Interact with the blockchain (mocked)
        std::string tx_hash = commit_to_blockchain(data_hash);

        // 4. Return the transaction hash
        crow::json::wvalue result;
        result["tx_hash"] = tx_hash;
        return crow::response(200, result);
    });

    app.port(18081).multithreaded().run();

    return 0;
}