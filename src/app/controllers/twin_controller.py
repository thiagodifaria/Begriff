from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from src.infra.persistence.database import get_db
from src.domains.insights.services import digital_twin_service
from src.domains.identity.dependencies import get_current_user
from src.infra.persistence import models
from src.infra.shared.schemas import digital_twin_schema

router = APIRouter()


@router.post("/twins/", response_model=digital_twin_schema.DigitalTwin)
def create_twin(twin_data: digital_twin_schema.DigitalTwinCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return digital_twin_service.create_digital_twin_for_user(db=db, twin_data=twin_data, user=current_user)


@router.get("/twins/", response_model=List[digital_twin_schema.DigitalTwin])
def get_twins(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return digital_twin_service.get_twins_for_user(db=db, user_id=current_user.id)
