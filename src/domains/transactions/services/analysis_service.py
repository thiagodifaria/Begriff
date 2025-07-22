import httpx
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from src.app.config import settings
from src.infra.persistence import models
from src.domains.risk.services import fraud_service
from src.domains.insights.services import carbon_service
from src.infra.persistence.repositories import analysis_repository

import datetime

def create_transactions_in_db(db: Session, transactions_data: List[Dict[str, Any]], user: models.User):
    for transaction_data in transactions_data:
        # Convert transaction_date string to date object
        transaction_data['transaction_date'] = datetime.datetime.strptime(transaction_data['transaction_date'], '%Y-%m-%d').date()
        db_transaction = models.Transaction(**transaction_data, owner=user)
        db.add(db_transaction)
    db.commit()


async def run_comprehensive_analysis(db: Session, transactions_data: List[Dict[str, Any]], user: models.User) -> models.FinancialAnalysis:
    create_transactions_in_db(db, transactions_data, user)

    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    fraud_results = fraud_service.analyze_for_fraud(transactions_data)
    carbon_results = carbon_service.calculate_carbon_footprint(transactions_data)
    
    gateway_result = {"error": "Gateway service unavailable"}
    try:
        # Convert date objects to strings for JSON serialization
        serializable_transactions_data = []
        for t_data in transactions_data:
            serializable_t_data = t_data.copy()
            if isinstance(serializable_t_data.get("transaction_date"), datetime.date):
                serializable_t_data["transaction_date"] = serializable_t_data["transaction_date"].isoformat()
            serializable_transactions_data.append(serializable_t_data)

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.GATEWAY_API_URL}/process", json={"transactions": serializable_transactions_data}, timeout=10.0)
            response.raise_for_status()
            gateway_result = response.json()
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")

    def convert_decimals_to_float(obj):
        if isinstance(obj, dict):
            return {k: convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimals_to_float(elem) for elem in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    final_report = {
        "summary": {
            "total_transactions": total_transactions,
            "total_amount": total_amount,
        },
        "fraud_analysis": fraud_results,
        "carbon_analysis": convert_decimals_to_float(carbon_results),
        "legacy_processing": gateway_result,
    }

    saved_analysis = analysis_repository.create_analysis(db=db, user=user, analysis_data=final_report)

    return saved_analysis


def get_user_analysis_history(db: Session, user_id: int) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_id(db=db, user_id=user_id)
