from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.infra.persistence.database import get_db
from src.domains.identity.dependencies import get_current_user
from src.domains.open_banking.services import sync_service
from src.infra.persistence.models import User
from src.infra.shared.schemas.open_banking_schema import ConnectAccountRequest
from src.domains.transactions.services import analysis_service
from src.infra.shared.schemas import analysis_schema

router = APIRouter(prefix="/banking")

@router.post("/account", status_code=status.HTTP_200_OK)
async def connect_account_and_sync(
    request_data: ConnectAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Connects a bank account and immediately synchronizes the user's transactions.
    """
    bank_id = request_data.id_banco
    if not bank_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'id_banco' is required."
        )

    # Conecta a conta bancária
    connection_result = await sync_service.connect_bank_account_to_user(
        user_id=str(current_user.id),
        bank_id=bank_id
    )

    # Sincroniza as transações
    sync_result = await sync_service.synchronize_transactions_for_user(
        db=db,
        user=current_user
    )

    return {
        "connection": connection_result,
        "sync_status": sync_result
    }

@router.post("/analysis", response_model=analysis_schema.FinancialAnalysis)
async def analyze_banking_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Triggers a new financial analysis from the user's already synchronized banking data.
    """
    try:
        return await analysis_service.run_banking_analysis(db=db, user=current_user)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to a required service: {e}"
        )

@router.get("/analysis/history", response_model=List[analysis_schema.FinancialAnalysis])
async def get_banking_analysis_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieves the history of banking-originated financial analyses for the user.
    """
    return analysis_service.get_user_analysis_history_by_type(db=db, user_id=current_user.id, analysis_type='BANKING')
