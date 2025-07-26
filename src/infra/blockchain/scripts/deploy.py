import json
import os
from web3 import Web3
from solcx import compile_source, install_solc
from dotenv import load_dotenv

load_dotenv()

def deploy_contract():
    # Install and set solc version
    install_solc('v0.8.0')

    # Connect to the blockchain node
    w3 = Web3(Web3.HTTPProvider(os.getenv("BLOCKCHAIN_NODE_URL")))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the blockchain node.")

    # Set the default account
    w3.eth.default_account = w3.eth.accounts[0]

    # Compile the Solidity contract
    with open("src/infra/blockchain/contracts/AuditTrail.sol", "r") as f:
        contract_source_code = f.read()

    compiled_sol = compile_source(contract_source_code, output_values=["abi", "bin"])
    contract_id, contract_interface = compiled_sol.popitem()
    bytecode = contract_interface["bin"]
    abi = contract_interface["abi"]

    # Save the ABI to a file
    with open("src/infra/blockchain/contracts/AuditTrail.json", "w") as f:
        json.dump(abi, f)

    # Deploy the contract
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = Contract.constructor().transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Contract deployed at: {tx_receipt.contractAddress}")
    return tx_receipt.contractAddress

if __name__ == "__main__":
    deploy_contract()
