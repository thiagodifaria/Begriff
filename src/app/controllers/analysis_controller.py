from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import csv
import io
from typing import List

from infra.persistence.database import get_db
from domains.identity.dependencies import get_current_user
from domains.transactions.services import analysis_service
from infra.persistence import models
from infra.shared.schemas import analysis_schema


from domains.edge_computing.orchestrator import EdgeOrchestrator

router = APIRouter()

# Initialize the EdgeOrchestrator at the module level
# edge_orchestrator = EdgeOrchestrator()



@router.post("/analysis/", response_model=analysis_schema.FinancialAnalysis)
async def create_analysis(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    contents = await file.read()
    decoded_content = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    transactions_data = [dict(row) for row in csv_reader]

    # Edge pre-processing step
    # edge_result = edge_orchestrator.dispatch_preprocessing_task(
    #     transactions_data=transactions_data,
    #     user_location="sa-east-1"
    # )
    # print(f"Edge pre-processing complete: {edge_result}")  # For now, we'll just print the result

    return await analysis_service.run_comprehensive_analysis(db=db, transactions_data=transactions_data, user=current_user)


@router.get("/analysis/", response_model=List[analysis_schema.FinancialAnalysis])
async def get_analysis_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return analysis_service.get_user_analysis_history(db=db, user_id=current_user.id)
