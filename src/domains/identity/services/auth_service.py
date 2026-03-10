from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.app.config import settings
from src.domains.exceptions import UserAlreadyExistsException
from src.infra.persistence import models
from src.infra.persistence.repositories import user_repository
from src.infra.shared.schemas import user_schema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_new_user(db: Session, user: user_schema.UserCreate):
    db_user = user_repository.get_user_by_email(db, email=user.email)
    if db_user:
        raise UserAlreadyExistsException(message="Email already registered")
    hashed_password = get_password_hash(user.password)
    return user_repository.create_user(db=db, user=user, hashed_password=hashed_password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = user_repository.get_user_by_email(db, email)
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "iat": now_utc, "nbf": now_utc, "typ": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def ensure_default_admin_user(db: Session) -> None:
    if not settings.ENABLE_DEFAULT_ADMIN:
        return
    admin_email = settings.DEFAULT_ADMIN_EMAIL
    admin_password = settings.DEFAULT_ADMIN_PASSWORD
    if not admin_email or not admin_password:
        return
    existing = user_repository.get_user_by_email(db, admin_email)
    if existing:
        return
    hashed_password = get_password_hash(admin_password)
    admin_user = user_schema.UserCreate(email=admin_email, password=admin_password)
    user_repository.create_user(db=db, user=admin_user, hashed_password=hashed_password)
