import json
import hashlib
from typing import Dict, Any
from web3 import Web3
from app.config import settings
import os

async def commit_analysis_to_blockchain(analysis_data: Dict[str, Any]) -> str:
    """
    Commits a record to the blockchain.

    Args:
        analysis_data: The analysis data to commit.

    Returns:
        The transaction hash.
    """
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_NODE_URL))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the blockchain node.")

    abi_path = os.path.join(os.path.dirname(__file__), 'contracts', 'AuditTrail.json')
    with open(abi_path, "r") as f:
        abi = json.load(f)

    contract = w3.eth.contract(address=settings.AUDIT_CONTRACT_ADDRESS, abi=abi)

    canonical_json = json.dumps(analysis_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    record_hash_bytes = hashlib.sha256(canonical_json).digest()
    record_hash_hex = record_hash_bytes.hex()

    tx_hash = contract.functions.addRecord(record_hash_hex).transact({'from': w3.eth.accounts[0]})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return receipt.transactionHash.hex()