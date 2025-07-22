from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.app.config import settings
from src.infra.persistence.database import get_db
from src.infra.persistence.repositories import user_repository
from src.infra.shared.schemas import user_schema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = user_repository.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user
