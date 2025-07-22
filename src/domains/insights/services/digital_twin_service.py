from sqlalchemy.orm import Session

from src.infra.persistence import models
from src.infra.shared.schemas import digital_twin_schema


def run_simulation(financial_profile: dict) -> dict:
    return {"initial_success_rate": 0.75, "message": "More detailed simulation pending."}


def create_digital_twin_for_user(db: Session, twin_data: digital_twin_schema.DigitalTwinCreate, user: models.User) -> models.DigitalTwin:
    simulation_results = run_simulation(twin_data.financial_profile)
    db_twin = models.DigitalTwin(
        name=twin_data.name,
        financial_profile=twin_data.financial_profile,
        simulation_results=simulation_results,
        owner=user
    )
    db.add(db_twin)
    db.commit()
    db.refresh(db_twin)
    return db_twin


def get_twins_for_user(db: Session, user_id: int) -> list[models.DigitalTwin]:
    return db.query(models.DigitalTwin).filter(models.DigitalTwin.user_id == user_id).all()
