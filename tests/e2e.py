import pytest
import httpx
import os
import uuid
import csv
import io

# Global configuration
BASE_URL = "http://localhost:8000"
test_state = {}

# Test definitions using pytest-dependency
@pytest.mark.dependency()
def test_register_user():
    """Registers a new unique user."""
    unique_email = f"testuser_{uuid.uuid4()}@example.com"
    password = "a_secure_password"
    
    response = httpx.post(f"{BASE_URL}/api/v1/users/", json={"email": unique_email, "password": password})
    
    assert response.status_code == 201
    
    test_state["email"] = unique_email
    test_state["password"] = password

@pytest.mark.dependency(depends=["test_register_user"])
def test_login_and_store_token():
    """Logs in the newly registered user and stores the authentication token."""
    credentials = {
        "username": test_state["email"],
        "password": test_state["password"]
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = httpx.post(f"{BASE_URL}/api/v1/token", data=credentials, headers=headers)
    
    assert response.status_code == 200
    
    token_data = response.json()
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    
    test_state["access_token"] = token_data["access_token"]

@pytest.mark.dependency(depends=["test_login_and_store_token"])
def test_connect_and_sync_account():
    """Connects a bank account and synchronizes transactions."""
    headers = {
        "Authorization": f"Bearer {test_state['access_token']}"
    }
    payload = {
        "id_banco": "santander"
    }
    
    response = httpx.post(f"{BASE_URL}/api/v1/banking/account", json=payload, headers=headers)
    
    assert response.status_code == 200
    
    sync_data = response.json()
    assert "transactions_synced" in sync_data
    assert sync_data["transactions_synced"] > 0

@pytest.mark.dependency(depends=["test_connect_and_sync_account"])
def test_banking_analysis_workflow():
    """Triggers and validates the banking analysis workflow."""
    headers = {
        "Authorization": f"Bearer {test_state['access_token']}"
    }
    
    response = httpx.post(f"{BASE_URL}/api/v1/banking/analysis", headers=headers)
    
    assert response.status_code == 200
    
    analysis_results = response.json()
    assert "summary" in analysis_results
    assert "total_transactions" in analysis_results["summary"]
    assert analysis_results["summary"]["total_transactions"] > 0

@pytest.mark.dependency(depends=["test_login_and_store_token"])
def test_csv_analysis_workflow():
    """Triggers and validates the CSV analysis workflow."""
    headers = {
        "Authorization": f"Bearer {test_state['access_token']}"
    }
    
    # Create an in-memory CSV file
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    writer.writerow(['transaction_date', 'description', 'amount', 'category'])
    writer.writerow(['2024-01-15', 'Test Purchase 1', '-50.75', 'Shopping'])
    writer.writerow(['2024-01-16', 'Test Deposit', '1200.00', 'Salary'])
    writer.writerow(['2024-01-17', 'Test Purchase 2', '-25.30', 'Groceries'])
    csv_output.seek(0)
    
    files = {'file': ('transactions.csv', csv_output, 'text/csv')}
    
    response = httpx.post(f"{BASE_URL}/api/v1/analysis/", headers=headers, files=files)
    
    assert response.status_code == 200
    
    analysis_results = response.json()
    assert "summary" in analysis_results
    assert "total_transactions" in analysis_results["summary"]
    assert analysis_results["summary"]["total_transactions"] > 0

@pytest.mark.dependency(depends=["test_banking_analysis_workflow", "test_csv_analysis_workflow"])
def test_analysis_history_endpoints():
    """Checks if both CSV and Banking analysis results are stored in history."""
    headers = {
        "Authorization": f"Bearer {test_state['access_token']}"
    }
    
    # Check CSV analysis history
    csv_history_response = httpx.get(f"{BASE_URL}/api/v1/analysis/", headers=headers)
    assert csv_history_response.status_code == 200
    csv_history = csv_history_response.json()
    assert isinstance(csv_history, list)
    assert len(csv_history) > 0
    
    # Check Banking analysis history
    banking_history_response = httpx.get(f"{BASE_URL}/api/v1/banking/analysis/history", headers=headers)
    assert banking_history_response.status_code == 200
    banking_history = banking_history_response.json()
    assert isinstance(banking_history, list)
    assert len(banking_history) > 0