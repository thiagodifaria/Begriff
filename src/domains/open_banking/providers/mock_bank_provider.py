from typing import Any, Dict, List

def get_transactions(user_id: int, auth_token: str) -> List[Dict[str, Any]]:
    """
    Simulates a call to a bank's Open Banking API to fetch transactions.
    In a real scenario, this would involve an HTTP request to the bank's API
    using the provided auth_token.
    """
    # The user_id and auth_token are ignored for this mock implementation.
    print(f"Fetching transactions for user {user_id} with token {auth_token[:10]}...")

    # Return a hardcoded list of transactions for demonstration purposes.
    return [
        {"description": "Monthly Salary", "amount": 5000.00, "category": "Income", "transaction_date": "2025-07-01"},
        {"description": "Grocery Shopping", "amount": -75.50, "category": "Food", "transaction_date": "2025-07-03"},
        {"description": "Electricity Bill", "amount": -120.00, "category": "Utilities", "transaction_date": "2025-07-05"},
        {"description": "Online Subscription", "amount": -15.00, "category": "Entertainment", "transaction_date": "2025-07-10"},
        {"description": "Dinner with Friends", "amount": -55.25, "category": "Social", "transaction_date": "2025-07-12"},
    ]
