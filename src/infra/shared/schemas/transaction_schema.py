from pydantic import BaseModel
from datetime import date
from decimal import Decimal


class TransactionBase(BaseModel):
    description: str
    amount: Decimal
    category: str
    transaction_date: date


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
