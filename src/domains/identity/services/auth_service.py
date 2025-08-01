from datetime import datetime, timedelta

from jose import jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.config import settings
from domains.exceptions import UserAlreadyExistsException
from infra.persistence.repositories import user_repository
from infra.shared.schemas import user_schema
from infra.persistence import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_new_user(db: Session, user: user_schema.UserCreate):
    db_user = user_repository.get_user_by_email(db, email=user.email)
    if db_user:
        raise UserAlreadyExistsException(message="Email already registered")
    hashed_password = get_password_hash(user.password)
    return user_repository.create_user(db=db, user=user, hashed_password=hashed_password)


from typing import Optional

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = user_repository.get_user_by_email(db, email)
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
