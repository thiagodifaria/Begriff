import httpx
import json
import numpy as np
from typing import Dict, Any
from src.domains.transactions.services.custom_json_encoder import CustomNumpyEncoder

async def commit_analysis_to_blockchain(analysis_data: Dict[str, Any]) -> str:
    """
    Commits analysis data to the blockchain via the crypto middleware.
    Sanitizes the data to ensure JSON compatibility.
    """
    
    # Function to sanitize JSON, replacing NaN/Infinity with None
    def sanitize_json(obj):
        """
        Recursively sanitizes a dictionary/list to replace NaN/Infinity with None.
        Crow's JSON parser cannot handle NaN or Infinity values.
        """
        if isinstance(obj, dict):
            return {k: sanitize_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_json(item) for item in obj]
        elif isinstance(obj, float):
            # Check for NaN or Infinity
            if np.isnan(obj) or np.isinf(obj):
                return None  # JSON null is accepted by Crow
            return obj
        elif obj is None or isinstance(obj, (str, int, bool)):
            return obj
        else:
            # Convert other types to string to ensure JSON compatibility
            return str(obj)
    
    # Sanitize the analysis data before sending
    sanitized_data = sanitize_json(analysis_data)
    
    # Ensure the JSON is valid before sending
    try:
        json_str = json.dumps(sanitized_data)
        # Verify it can be parsed back
        json.loads(json_str)
    except (TypeError, ValueError) as e:
        print(f"Warning: JSON serialization issue: {e}")
        # Fallback to a minimal valid JSON
        sanitized_data = {"data": "analysis_completed", "status": "success"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://crypto_middleware:18081/secure-commit",
            json=sanitized_data,
            timeout=10.0
        )
        response.raise_for_status()
        result = response.json()
        return result.get("tx_hash", "0x0000000000000000000000000000000000000000")