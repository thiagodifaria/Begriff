from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime, Numeric, Date, Text
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
    ui_settings = relationship("UserUiSetting", back_populates="owner")
    reports = relationship("GeneratedReport", back_populates="owner")
    report_schedules = relationship("ReportSchedule", back_populates="owner")


from typing import Optional


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
    source = Column(String, nullable=False, index=True)

    owner = relationship("User", back_populates="transactions")


class FinancialAnalysis(Base):
    __tablename__ = "financial_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_results = Column(JSON, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    blockchain_tx_hash = Column(String, nullable=True, index=True)
    analysis_type = Column(String, nullable=False, index=True)

    owner = relationship("User", back_populates="analyses")


class UserUiSetting(Base):
    __tablename__ = "user_ui_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True)
    settings = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="ui_settings")


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    report_type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    owner = relationship("User", back_populates="reports")


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String, nullable=False, index=True)
    frequency = Column(String, nullable=False)
    recipients = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    owner = relationship("User", back_populates="report_schedules")
