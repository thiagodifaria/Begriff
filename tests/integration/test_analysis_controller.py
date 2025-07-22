import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.app.main import app
from src.infra.persistence.database import Base, get_db
from src.infra.persistence import models
from src.domains.identity.dependencies import get_current_user

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create a test user within this session
        user = models.User(email="test@test.com", hashed_password="test")
        db.add(user)
        db.commit()
        db.refresh(user)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_analysis(db_session):
    def override_get_db_for_test():
        yield db_session

    def override_get_current_user_for_test(db: Session = Depends(override_get_db_for_test)):
        user = db.query(models.User).filter(models.User.email == "test@test.com").first()
        return user

    # Store original dependencies
    original_get_db = app.dependency_overrides.get(get_db)
    original_get_current_user = app.dependency_overrides.get(get_current_user)

    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db_for_test
    app.dependency_overrides[get_current_user] = override_get_current_user_for_test

    try:
        csv_data = "description,amount,category,transaction_date\nTest transaction,100.00,Test,2025-07-22"
        files = {"file": ("test.csv", csv_data, "text/csv")}
        response = client.post("/api/v1/analysis/", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_results"]["summary"]["total_transactions"] == 1
        assert data["analysis_results"]["summary"]["total_amount"] == 100.0
        assert "fraud_analysis" in data["analysis_results"]
        assert "carbon_analysis" in data["analysis_results"]
        assert "legacy_processing" in data["analysis_results"]

        analysis_in_db = db_session.query(models.FinancialAnalysis).first()
        assert analysis_in_db is not None
        assert analysis_in_db.owner.email == "test@test.com"
    finally:
        # Restore original dependencies
        if original_get_db:
            app.dependency_overrides[get_db] = original_get_db
        else:
            del app.dependency_overrides[get_db]
        if original_get_current_user:
            app.dependency_overrides[get_current_user] = original_get_current_user
        else:
            del app.dependency_overrides[get_current_user]