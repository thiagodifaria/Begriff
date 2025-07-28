import httpx
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from domains.transactions.services import analysis_service
from infra.persistence.models import User, FinancialAnalysis


async def synchronize_bank_data_and_analyze(
    db: Session, user: User
) -> FinancialAnalysis:
    """
    Orchestrates the workflow of fetching bank data from the mock Open Banking
    provider and running a comprehensive financial analysis.

    Args:
        db: The database session.
        user: The user for whom to synchronize data.

    Returns:
        The newly created and persisted financial analysis report.
    """
    async with httpx.AsyncClient() as client:
        # Create a dummy authorization header
        headers = {"Authorization": "Bearer fake-token"}

        # Step 1: Fetch Accounts
        try:
            accounts_response = await client.get(
                f"{settings.OPEN_BANKING_MOCK_URL}/accounts",
                params={"user_id": user.id},
                headers=headers,
            )
            accounts_response.raise_for_status()  # Raise an exception for bad status codes
            accounts = accounts_response.json()
        except httpx.RequestError as e:
            # Handle connection errors or invalid responses
            print(f"Error fetching accounts: {e}")
            return None  # Or raise a custom exception

        # Step 2: Fetch Transactions for each account
        all_transactions: List[Dict[str, Any]] = []
        for account in accounts:
            try:
                transactions_response = await client.get(
                    f"{settings.OPEN_BANKING_MOCK_URL}/accounts/{account['account_id']}/transactions",
                    headers=headers,
                )
                transactions_response.raise_for_status()
                transactions = transactions_response.json()
                all_transactions.extend(transactions)
            except httpx.RequestError as e:
                # Handle errors for individual account transaction fetching
                print(f"Error fetching transactions for account {account['account_id']}: {e}")
                # Decide if you want to continue with partial data or fail the process
                continue

        # Step 3: Trigger Comprehensive Analysis
        if not all_transactions:
            print("No transactions were fetched, skipping analysis.")
            return None # Or handle as appropriate

        analysis_report = await analysis_service.run_comprehensive_analysis(
            db=db, transactions_data=all_transactions, user=user
        )

        return analysis_report
