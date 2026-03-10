import asyncio
import datetime
from decimal import Decimal
from typing import Any, Dict, List

import httpx
from sqlalchemy.orm import Session

from src.app.config import settings
from src.domains.exceptions import AnalysisGatewayError
from src.domains.insights.services import carbon_service, generative_ai_service
from src.domains.risk.services import fraud_service
from src.infra.blockchain import auditor_service
from src.infra.persistence import models
from src.infra.persistence.repositories import analysis_repository


def create_transactions_in_db(db: Session, transactions_data: List[Dict[str, Any]], user: models.User):
    for transaction_data in transactions_data:
        transaction_data["transaction_date"] = datetime.datetime.strptime(
            transaction_data["transaction_date"], "%Y-%m-%d"
        ).date()
        transaction_data["source"] = "CSV_UPLOAD"
        db_transaction = models.Transaction(**transaction_data, owner=user)
        db.add(db_transaction)
    db.commit()


def _convert_decimals_to_float(obj: Any):
    if isinstance(obj, dict):
        return {k: _convert_decimals_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_decimals_to_float(elem) for elem in obj]
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def _normalize_transactions(transactions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serializable_transactions_data: List[Dict[str, Any]] = []
    for t_data in transactions_data:
        serializable_t_data = t_data.copy()
        if "id" in serializable_t_data:
            serializable_t_data["id"] = int(serializable_t_data["id"])
        if "amount" in serializable_t_data:
            serializable_t_data["amount"] = float(serializable_t_data["amount"])
        if isinstance(serializable_t_data.get("transaction_date"), datetime.date):
            serializable_t_data["transaction_date"] = serializable_t_data["transaction_date"].isoformat()
        serializable_transactions_data.append(serializable_t_data)
    return serializable_transactions_data


async def _call_gateway(transactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        payload = {"transactions": _normalize_transactions(transactions_data)}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.GATEWAY_API_URL}/process", json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        raise AnalysisGatewayError(f"An error occurred while requesting {exc.request.url!r}.")


def _build_report(
    total_transactions: int,
    total_amount: float,
    fraud_results: Dict[str, Any],
    carbon_results: Dict[str, Any],
    gateway_result: Dict[str, Any],
    reconciliation_summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    report = {
        "summary": {"total_transactions": total_transactions, "total_amount": total_amount},
        "fraud_analysis": fraud_results,
        "carbon_analysis": _convert_decimals_to_float(carbon_results),
        "legacy_processing": gateway_result,
    }
    if reconciliation_summary is not None:
        report["cobol_reconciliation"] = reconciliation_summary
    return report


async def run_comprehensive_analysis(
    db: Session, transactions_data: List[Dict[str, Any]], user: models.User
) -> models.FinancialAnalysis:
    create_transactions_in_db(db, transactions_data, user)
    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    tasks = [
        fraud_service.analyze_for_fraud(transactions_data),
        carbon_service.calculate_carbon_footprint(transactions_data),
        _call_gateway(transactions_data),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    fraud_results = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
    carbon_results = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
    gateway_result = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}

    final_report = _build_report(total_transactions, total_amount, fraud_results, carbon_results, gateway_result)
    final_report["generative_summary"] = await generative_ai_service.generate_personalized_report(
        user=user, analysis_data=final_report
    )

    saved_analysis = analysis_repository.create_analysis(
        db=db, user=user, analysis_data=final_report, analysis_type="CSV"
    )
    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)
    return analysis_repository.add_blockchain_hash_to_analysis(
        db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash
    )


async def run_banking_analysis(db: Session, user: models.User) -> models.FinancialAnalysis:
    transactions = analysis_repository.get_transactions_by_source_prefix(db, user.id, "_SYNC")
    transactions_data = [
        {
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "category": t.category,
            "transaction_date": t.transaction_date,
            "user_id": t.user_id,
            "source": t.source,
        }
        for t in transactions
    ]

    reconciliation_summary = {}
    try:
        cobol_ready_data = [
            {
                "id": str(t.get("id", "")),
                "date": t.get("transaction_date").isoformat() if t.get("transaction_date") else "",
                "amount": float(t.get("amount", 0.0)),
                "type": str(t.get("type", "DEBIT")),
                "category": str(t.get("category", "")),
                "description": str(t.get("description", "")),
            }
            for t in transactions_data
        ]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://reconciliation_middleware:18080/reconcile",
                json={"transactions": cobol_ready_data},
                timeout=30.0,
            )
            response.raise_for_status()
            reconciliation_summary = response.json()
    except httpx.RequestError as exc:
        reconciliation_summary = {"error": f"Failed to connect to reconciliation middleware: {exc}"}
    except Exception as e:
        reconciliation_summary = {"error": f"An unexpected error occurred during reconciliation: {e}"}

    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    tasks = [
        fraud_service.analyze_for_fraud(transactions_data),
        carbon_service.calculate_carbon_footprint(transactions_data),
        _call_gateway(transactions_data),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    fraud_results = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
    carbon_results = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
    gateway_result = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}

    final_report = _build_report(
        total_transactions,
        total_amount,
        fraud_results,
        carbon_results,
        gateway_result,
        reconciliation_summary=reconciliation_summary,
    )
    final_report["generative_summary"] = await generative_ai_service.generate_personalized_report(
        user=user, analysis_data=final_report
    )

    saved_analysis = analysis_repository.create_analysis(
        db=db, user=user, analysis_data=final_report, analysis_type="BANKING"
    )
    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)
    return analysis_repository.add_blockchain_hash_to_analysis(
        db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash
    )


def get_user_analysis_history(db: Session, user_id: int) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_id(db=db, user_id=user_id)


def get_user_analysis_history_by_type(db: Session, user_id: int, analysis_type: str) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_and_type(db=db, user_id=user_id, analysis_type=analysis_type)
