from uuid import UUID
from pydantic import BaseModel, Field
from datetime import date
import uuid

class Balance(BaseModel):
    amount: float
    currency: str

class Account(BaseModel):
    account_id: UUID = Field(default_factory=uuid.uuid4)
    type: str
    balance: Balance

class Transaction(BaseModel):
    transaction_id: UUID = Field(default_factory=uuid.uuid4)
    amount: float
    description: str
    transaction_date: date
