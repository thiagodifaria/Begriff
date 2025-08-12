import httpx
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime

from src.app.config import settings
from src.infra.persistence.models import User, Transaction as TransactionModel


async def connect_bank_account_to_user(user_id: str, bank_id: str) -> Dict[str, Any]:
    """
    Connects a bank account to a user by calling the mock Open Banking provider.

    Args:
        user_id: The ID of the user.
        bank_id: The ID of the bank to connect.

    Returns:
        The response from the mock Open Banking provider.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.OPEN_BANKING_MOCK_URL}/conectar-conta",
                json={"id_usuario": user_id, "id_banco": bank_id},
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to the Open Banking service: {e}",
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from Open Banking service: {e.response.text}",
            )


async def synchronize_transactions_for_user(db: Session, user: User) -> dict:
    """
    Sincroniza as transações do usuário a partir do mock do Open Banking.
    """
    async with httpx.AsyncClient() as client:
        try:
            # First, get all connected accounts for the user
            accounts_response = await client.get(
                f"{settings.OPEN_BANKING_MOCK_URL}/accounts",
                params={"id_usuario": str(user.id)}
            )
            accounts_response.raise_for_status()
            accounts = accounts_response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to the Open Banking service: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from Open Banking service: {e.response.text}"
            )

        all_transactions: List[Dict[str, Any]] = []
        for account in accounts:
            account_id = account.get("id_conta")
            if not account_id:
                continue

            try:
                # Then, fetch transactions for each account
                transactions_response = await client.get(
                    f"{settings.OPEN_BANKING_MOCK_URL}/accounts/{account_id}/transactions"
                )
                transactions_response.raise_for_status()
                transactions = transactions_response.json()
                
                for trans in transactions:
                    trans['id_banco'] = account.get('id_banco')

                all_transactions.extend(transactions)
            except httpx.RequestError as e:
                # Log the error but continue, to allow for partial data processing
                print(f"Warning: Could not fetch transactions for account {account_id}: {e}")
                continue
            except httpx.HTTPStatusError as e:
                # Log the error but continue
                print(f"Warning: The Open Banking service returned an error for account {account_id}: {e.response.text}")
                continue
        
        for transaction in all_transactions:
            db_transaction = TransactionModel(
                description=transaction['description'],
                amount=Decimal(transaction['amount']),
                category=transaction['category'],
                transaction_date=datetime.strptime(transaction['transaction_date'], '%Y-%m-%d').date(),
                user_id=user.id,
                source=f"{transaction['id_banco']}_SYNC"
            )
            db.add(db_transaction)
        
        db.commit()
        
        return {
            "message": "Sincronização de transações concluída.",
            "transactions_synced": len(all_transactions)
        }