import asyncio
import httpx
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import datetime

from src.app.config import settings
from src.infra.persistence import models
from src.domains.risk.services import fraud_service
from src.domains.insights.services import carbon_service, generative_ai_service
from src.infra.persistence.repositories import analysis_repository
from src.infra.blockchain import auditor_service
from src.domains.exceptions import AnalysisGatewayError

import asyncio
import httpx
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import datetime

from src.app.config import settings
from src.infra.persistence import models
from src.domains.risk.services import fraud_service
from src.domains.insights.services import carbon_service, generative_ai_service
from src.infra.persistence.repositories import analysis_repository
from src.infra.blockchain import auditor_service
from src.domains.exceptions import AnalysisGatewayError

def create_transactions_in_db(db: Session, transactions_data: List[Dict[str, Any]], user: models.User):
    for transaction_data in transactions_data:
        transaction_data['transaction_date'] = datetime.datetime.strptime(transaction_data['transaction_date'], '%Y-%m-%d').date()
        transaction_data['source'] = 'CSV_UPLOAD'
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
                
                # Garante a conversão de 'id' para inteiro
                if 'id' in serializable_t_data:
                    serializable_t_data['id'] = int(serializable_t_data['id'])
                
                # Garante a conversão de 'amount' para float
                if 'amount' in serializable_t_data:
                    serializable_t_data['amount'] = float(serializable_t_data['amount'])

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

    saved_analysis = analysis_repository.create_analysis(db=db, user=user, analysis_data=final_report, analysis_type='CSV')

    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)

    updated_analysis = analysis_repository.add_blockchain_hash_to_analysis(db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash)

    return updated_analysis

async def run_banking_analysis(db: Session, user: models.User) -> models.FinancialAnalysis:
    transactions = analysis_repository.get_transactions_by_source_prefix(db, user.id, '_SYNC')
    
    transactions_data = [
        {
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "category": t.category,
            "transaction_date": t.transaction_date,
            "user_id": t.user_id,
            "source": t.source
        }
        for t in transactions
    ]

    # Fase 3: Chamar o middleware de reconciliação C++
    reconciliation_summary = {}
    try:
        # Prepara os dados para o formato esperado pelo COBOL (string)
        cobol_ready_data = []
        for t in transactions_data:
            cobol_ready_data.append({
                "id": str(t.get("id", "")),
                "date": t.get("transaction_date").isoformat() if t.get("transaction_date") else "",
                "amount": float(t.get("amount", 0.0)),
                "type": str(t.get("type", "DEBIT")), # Assumindo um padrão
                "category": str(t.get("category", "")),
                "description": str(t.get("description", ""))
            })

        async with httpx.AsyncClient() as client:
            # O endpoint do middleware C++
            response = await client.post("http://reconciliation_middleware:18080/reconcile", json={"transactions": cobol_ready_data}, timeout=30.0)
            response.raise_for_status()
            reconciliation_summary = response.json()
    except httpx.RequestError as exc:
        reconciliation_summary = {"error": f"Failed to connect to reconciliation middleware: {exc}"}
    except Exception as e:
        reconciliation_summary = {"error": f"An unexpected error occurred during reconciliation: {e}"}


    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    async def gateway_task():
        try:
            serializable_transactions_data = []
            for t_data in transactions_data:
                serializable_t_data = t_data.copy()
                
                if 'id' in serializable_t_data:
                    serializable_t_data['id'] = int(serializable_t_data['id'])
                
                if 'amount' in serializable_t_data:
                    serializable_t_data['amount'] = float(serializable_t_data['amount'])

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
        "cobol_reconciliation": reconciliation_summary, # Adicionado Fase 3
        "fraud_analysis": fraud_results,
        "carbon_analysis": convert_decimals_to_float(carbon_results),
        "legacy_processing": gateway_result,
    }

    generative_insights = await generative_ai_service.generate_personalized_report(user=user, analysis_data=final_report)
    final_report['generative_summary'] = generative_insights

    saved_analysis = analysis_repository.create_analysis(db=db, user=user, analysis_data=final_report, analysis_type='BANKING')

    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)

    updated_analysis = analysis_repository.add_blockchain_hash_to_analysis(db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash)

    return updated_analysis

def get_user_analysis_history(db: Session, user_id: int) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_id(db=db, user_id=user_id)

def get_user_analysis_history_by_type(db: Session, user_id: int, analysis_type: str) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_and_type(db=db, user_id=user_id, analysis_type=analysis_type)


async def run_comprehensive_analysis(db: Session, transactions_data: List[Dict[str, Any]], user: models.User) -> models.FinancialAnalysis:
    create_transactions_in_db(db, transactions_data, user)

    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    async def gateway_task():
        try:
            serializable_transactions_data = []
            for t_data in transactions_data:
                serializable_t_data = t_data.copy()
                
                # Garante a conversão de 'id' para inteiro
                if 'id' in serializable_t_data:
                    serializable_t_data['id'] = int(serializable_t_data['id'])
                
                # Garante a conversão de 'amount' para float
                if 'amount' in serializable_t_data:
                    serializable_t_data['amount'] = float(serializable_t_data['amount'])

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

    saved_analysis = analysis_repository.create_analysis(db=db, user=user, analysis_data=final_report, analysis_type='CSV')

    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)

    updated_analysis = analysis_repository.add_blockchain_hash_to_analysis(db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash)

    return updated_analysis

async def run_banking_analysis(db: Session, user: models.User) -> models.FinancialAnalysis:
    transactions = analysis_repository.get_transactions_by_source_prefix(db, user.id, '_SYNC')
    
    transactions_data = [
        {
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "category": t.category,
            "transaction_date": t.transaction_date,
            "user_id": t.user_id,
            "source": t.source
        }
        for t in transactions
    ]

    # Fase 3: Chamar o middleware de reconciliação C++
    reconciliation_summary = {}
    try:
        # Prepara os dados para o formato esperado pelo COBOL (string)
        cobol_ready_data = []
        for t in transactions_data:
            cobol_ready_data.append({
                "id": str(t.get("id", "")),
                "date": t.get("transaction_date").isoformat() if t.get("transaction_date") else "",
                "amount": float(t.get("amount", 0.0)),
                "type": str(t.get("type", "DEBIT")), # Assumindo um padrão
                "category": str(t.get("category", "")),
                "description": str(t.get("description", ""))
            })

        async with httpx.AsyncClient() as client:
            # O endpoint do middleware C++
            response = await client.post("http://reconciliation_middleware:18080/reconcile", json={"transactions": cobol_ready_data}, timeout=30.0)
            response.raise_for_status()
            reconciliation_summary = response.json()
    except httpx.RequestError as exc:
        reconciliation_summary = {"error": f"Failed to connect to reconciliation middleware: {exc}"}
    except Exception as e:
        reconciliation_summary = {"error": f"An unexpected error occurred during reconciliation: {e}"}


    total_transactions = len(transactions_data)
    total_amount = sum(float(t["amount"]) for t in transactions_data)

    async def gateway_task():
        try:
            serializable_transactions_data = []
            for t_data in transactions_data:
                serializable_t_data = t_data.copy()
                
                if 'id' in serializable_t_data:
                    serializable_t_data['id'] = int(serializable_t_data['id'])
                
                if 'amount' in serializable_t_data:
                    serializable_t_data['amount'] = float(serializable_t_data['amount'])

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
        "cobol_reconciliation": reconciliation_summary, # Adicionado Fase 3
        "fraud_analysis": fraud_results,
        "carbon_analysis": convert_decimals_to_float(carbon_results),
        "legacy_processing": gateway_result,
    }

    generative_insights = await generative_ai_service.generate_personalized_report(user=user, analysis_data=final_report)
    final_report['generative_summary'] = generative_insights

    saved_analysis = analysis_repository.create_analysis(db=db, user=user, analysis_data=final_report, analysis_type='BANKING')

    tx_hash = await auditor_service.commit_analysis_to_blockchain(analysis_data=final_report)

    updated_analysis = analysis_repository.add_blockchain_hash_to_analysis(db=db, analysis_id=saved_analysis.id, tx_hash=tx_hash)

    return updated_analysis

def get_user_analysis_history(db: Session, user_id: int) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_id(db=db, user_id=user_id)

def get_user_analysis_history_by_type(db: Session, user_id: int, analysis_type: str) -> List[models.FinancialAnalysis]:
    return analysis_repository.get_analyses_by_user_and_type(db=db, user_id=user_id, analysis_type=analysis_type)