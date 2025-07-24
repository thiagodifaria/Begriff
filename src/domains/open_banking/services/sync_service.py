from sqlalchemy.orm import Session

from src.domains.open_banking.providers import mock_bank_provider
from src.domains.transactions.services import analysis_service
from src.infra.persistence import models


async def synchronize_bank_data_and_analyze(
    db: Session, user: models.User
) -> models.FinancialAnalysis:
    """
    Orchestrates the workflow of fetching bank data and running analysis.

    Args:
        db: The database session.
        user: The user for whom to synchronize data.

    Returns:
        The newly created and persisted financial analysis report.
    """
    # 1. Simulate authenticating with the bank
    auth_token = "dummy_oauth2_token"

    # 2. Fetch transaction data from the mock provider
    transactions_data = mock_bank_provider.get_transactions(
        user_id=user.id, auth_token=auth_token
    )

    # 3. Run the existing comprehensive analysis service with the new data
    analysis_report = await analysis_service.run_comprehensive_analysis(
        db=db, transactions_data=transactions_data, user=user
    )

    return analysis_report
