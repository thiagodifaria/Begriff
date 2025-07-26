from fastapi import FastAPI, Depends, HTTPException, Header
from typing import List
from uuid import UUID
from . import data_generator
from .models import Account, Transaction

app = FastAPI()

async def get_token_header(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

@app.get("/accounts", response_model=List[Account])
def get_accounts(user_id: int, token: str = Depends(get_token_header)):
    user_data = data_generator.get_or_create_user_data(user_id)
    return user_data["accounts"]

@app.get("/accounts/{account_id}/transactions", response_model=List[Transaction])
async def get_transactions_for_account(account_id: UUID, user_id: int, token: str = Depends(get_token_header)):
    user_data = data_generator.get_or_create_user_data(user_id)
    if account_id not in user_data["transactions"]:
        raise HTTPException(status_code=404, detail="Account not found")
    return user_data["transactions"][account_id]