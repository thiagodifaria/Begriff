from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.app.config import settings


def get_connect_args():
    if settings.DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("postgresql"):
        return {"sslmode": settings.DATABASE_SSL_MODE}
    return {}

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=get_connect_args()
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_user_rls_context(db, user_id: int):
    if settings.DATABASE_URL.startswith("postgresql"):
        db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": str(user_id)})
