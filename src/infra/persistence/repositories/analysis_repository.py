from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.infra.persistence.models import FinancialAnalysis, User, Transaction


def create_analysis(db: Session, user: User, analysis_data: Dict[str, Any], analysis_type: str) -> FinancialAnalysis:
    db_analysis = FinancialAnalysis(
        analysis_results=analysis_data,
        owner=user,
        analysis_type=analysis_type
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analyses_by_user_id(db: Session, user_id: int) -> List[FinancialAnalysis]:
    return db.query(FinancialAnalysis).filter(FinancialAnalysis.user_id == user_id).all()

def get_analyses_by_user_and_type(db: Session, user_id: int, analysis_type: str) -> List[FinancialAnalysis]:
    return db.query(FinancialAnalysis).filter(
        FinancialAnalysis.user_id == user_id,
        FinancialAnalysis.analysis_type == analysis_type
    ).all()


def add_blockchain_hash_to_analysis(db: Session, analysis_id: int, tx_hash: str) -> FinancialAnalysis:
    db_analysis = db.query(FinancialAnalysis).filter(FinancialAnalysis.id == analysis_id).first()
    if db_analysis:
        db_analysis.blockchain_tx_hash = tx_hash
        db.commit()
        db.refresh(db_analysis)
    return db_analysis

def get_transactions_by_user(db: Session, user_id: int) -> List[Transaction]:
    """
    Busca todas as transações de um usuário no banco de dados.
    """
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()

def get_transactions_by_source_prefix(db: Session, user_id: int, source_prefix: str) -> List[Transaction]:
    return db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.source.like(f"{source_prefix}%")
    ).all()