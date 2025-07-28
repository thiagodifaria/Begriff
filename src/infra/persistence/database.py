from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

def get_connect_args():
    """Retorna connect_args apropriados baseado no tipo de banco"""
    if settings.DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    elif settings.DATABASE_URL.startswith("postgresql"):
        return {}
    else:
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