from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class FinancialAnalysisBase(BaseModel):
    pass

class FinancialAnalysisCreate(FinancialAnalysisBase):
    pass

class FinancialAnalysis(FinancialAnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    analysis_results: Dict[str, Any]

    class Config:
        from_attributes = True
