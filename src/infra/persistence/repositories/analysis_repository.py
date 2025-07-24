from sqlalchemy.orm import Session
from src.infra.persistence import models
from typing import List


def create_analysis(db: Session, user: models.User, analysis_data: dict) -> models.FinancialAnalysis:
    db_analysis = models.FinancialAnalysis(
        analysis_results=analysis_data,
        owner=user
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analyses_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.FinancialAnalysis]:
    return db.query(models.FinancialAnalysis).filter(models.FinancialAnalysis.user_id == user_id).order_by(models.FinancialAnalysis.created_at.desc()).offset(skip).limit(limit).all()

def add_blockchain_hash_to_analysis(db: Session, analysis_id: int, tx_hash: str) -> models.FinancialAnalysis:
    db_analysis = db.query(models.FinancialAnalysis).filter(models.FinancialAnalysis.id == analysis_id).first()
    if db_analysis:
        db_analysis.blockchain_tx_hash = tx_hash
        db.commit()
        db.refresh(db_analysis)
    return db_analysis
