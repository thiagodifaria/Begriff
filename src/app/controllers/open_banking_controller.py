from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from domains.identity.dependencies import get_current_user
from infra.persistence.database import get_db
from domains.open_banking.services import sync_service
from infra.persistence import models
from infra.shared.schemas import analysis_schema

router = APIRouter()


@router.post(
    "/open-banking/sync",
    response_model=analysis_schema.FinancialAnalysis,
    summary="Synchronize Bank Account and Trigger Analysis",
    description="Initiates a synchronization with the user's bank account to fetch recent transactions and immediately triggers a new comprehensive financial analysis on that data.",
)
async def sync_bank_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.FinancialAnalysis:
    """
    Endpoint to trigger the bank data synchronization and analysis process.

    Args:
        db: The database session, injected by FastAPI.
        current_user: The authenticated user, injected by the security dependency.

    Returns:
        The resulting financial analysis report.
    """
    analysis_report = await sync_service.synchronize_bank_data_and_analyze(
        db=db, user=current_user
    )
    return analysis_report
