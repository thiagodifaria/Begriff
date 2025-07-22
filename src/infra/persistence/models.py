from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime, Numeric, Date
from sqlalchemy.orm import relationship
import datetime

from src.infra.persistence.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    twins = relationship("DigitalTwin", back_populates="owner")
    transactions = relationship("Transaction", back_populates="owner")
    analyses = relationship("FinancialAnalysis", back_populates="owner")


class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    financial_profile = Column(JSON)
    simulation_results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="twins")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Numeric(10, 2))
    category = Column(String, index=True)
    transaction_date = Column(Date)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="transactions")


class FinancialAnalysis(Base):
    __tablename__ = "financial_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_results = Column(JSON, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="analyses")
