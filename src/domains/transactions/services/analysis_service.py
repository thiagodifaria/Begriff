import asyncio
import httpx
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import datetime

from app.config import settings
from infra.persistence import models
from domains.risk.services import fraud_service
from domains.insights.services import carbon_service, generative_ai_service
from infra.persistence.repositories import analysis_repository
from infra.blockchain import auditor_service
from domains.exceptions import AnalysisGatewayError

def create_transactions_in_db(db: Session, transactions_data: List[Dict[str, Any]], user: models.User):
    for transaction_data in transactions_data:
        transaction_data['transaction_date'] = datetime.datetime.strptime(transaction_data['transaction_date'], '%Y-%m-%d').date()
        db_transaction = models.Transaction(**transaction_data, owner=user)
        db.add(db_transaction)
    db.commit()

async def run_comprehensive_analysis(db: Session, transactions_data: List[Dict[str, Any]], user: models.User) -> models.FinancialAnalysis:
    create_transactions_in_db(db, transactions_data, user)

    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    async def gateway_task():
        try:
            serializable_transactions_data = []
            for t_data in transactions_data:
                serializable_t_data = t_data.copy()
                if isinstance(serializable_t_data.get("transaction_date"), datetime.date):
                    serializable_t_data["transaction_date"] = serializable_t_data["transaction_date"].isoformat()
                serializable_transactions_data.append(serializable_t_data)

            async with httpx.AsyncClient() as client:
                response = await client.post(f"{settings.GATEWAY_API_URL}/process", json={"transactions": serializable_transactions_data}, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as exc:
            raise AnalysisGatewayError(f"An error occurred while requesting {exc.request.url!r}.")

    tasks = [
        fraud_service.analyze_for_fraud(transactions_data),
        carbon_service.calculate_carbon_footprint(transactions_data),
        gateway_task()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    fraud_results = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
    carbon_results = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
    gateway_result = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}

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

    generative_insights = await generative_ai_service.generate_personalized_report(user=user, analysis_data=final_report)
    final_report['generative_summary'] = generative_insights

    saved_analysis = analysis_repository.create_analysis(db=db, user=user, analysis_data=final_report)

    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)

    updated_analysis = analysis_repository.add_blockchain_hash_to_analysis(db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash)

    return updated_analysis

def get_user_analysis_history(db: Session, user_id: int) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_id(db=db, user_id=user_id)