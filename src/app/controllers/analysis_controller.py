from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import csv
import io
from typing import List

from src.infra.persistence.database import get_db
from src.domains.identity.dependencies import get_current_user
from src.domains.transactions.services import analysis_service
from src.infra.persistence import models
from src.infra.shared.schemas import analysis_schema

router = APIRouter()


@router.post("/analysis/", response_model=analysis_schema.FinancialAnalysis)
async def create_analysis(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    contents = await file.read()
    decoded_content = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    transactions_data = [row for row in csv_reader]

    return await analysis_service.run_comprehensive_analysis(db=db, transactions_data=transactions_data, user=current_user)


@router.get("/analysis/", response_model=List[analysis_schema.FinancialAnalysis])
async def get_analysis_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return analysis_service.get_user_analysis_history(db=db, user_id=current_user.id)
