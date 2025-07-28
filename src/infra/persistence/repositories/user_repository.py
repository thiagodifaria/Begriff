from sqlalchemy.orm import Session

from infra.persistence import models
from infra.shared.schemas import user_schema
from typing import Optional

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: user_schema.UserCreate, hashed_password: str) -> models.User:
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
