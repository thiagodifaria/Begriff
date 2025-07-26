import random
import uuid
from datetime import date, timedelta
from .models import Account, Balance, Transaction

MOCK_DB = {}

def get_or_create_user_data(user_id: int) -> dict:
    if user_id not in MOCK_DB:
        MOCK_DB[user_id] = {
            "accounts": [
                Account(type="CHECKING", balance=Balance(amount=random.uniform(1000, 5000), currency="BRL")),
                Account(type="CREDIT_CARD", balance=Balance(amount=random.uniform(-500, -100), currency="BRL")),
            ],
            "transactions": {},
        }
        for account in MOCK_DB[user_id]["accounts"]:
            MOCK_DB[user_id]["transactions"][account.account_id] = _generate_transactions_for_account()
    return MOCK_DB[user_id]

def _generate_transactions_for_account() -> list[Transaction]:
    transactions = []
    today = date.today()
    for _ in range(random.randint(5, 20)):
        transaction_date = today - timedelta(days=random.randint(0, 90))
        transactions.append(
            Transaction(
                amount=random.uniform(-1000, 1000),
                description=random.choice(["Groceries", "Salary", "Restaurant", "Online Shopping", "Utilities"]),
                transaction_date=transaction_date,
            )
        )
    return transactions
