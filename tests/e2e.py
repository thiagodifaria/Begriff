import os
import uuid
from typing import Any, Dict

import httpx


BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
USERNAME = os.getenv("E2E_USERNAME", "admin")
PASSWORD = os.getenv("E2E_PASSWORD", "admin")
TIMEOUT = float(os.getenv("E2E_TIMEOUT_SECONDS", "60"))


def _assert_status(response: httpx.Response, expected: int) -> None:
    assert response.status_code == expected, (
        f"Expected {expected}, got {response.status_code}. "
        f"URL={response.request.method} {response.request.url} "
        f"BODY={response.text[:1000]}"
    )


def _login(client: httpx.Client) -> str:
    response = client.post(
        f"{BASE_URL}/api/v1/token",
        data={"username": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    _assert_status(response, 200)
    payload = response.json()
    assert payload.get("token_type") == "bearer"
    assert payload.get("access_token")
    return payload["access_token"]


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_e2e_simulation_and_ui_backing_endpoints():
    """
    End-to-end scenario focused on simulated data and UI-backed endpoints.
    Requires backend running with default admin/admin user enabled.
    """
    with httpx.Client(timeout=TIMEOUT) as client:
        # Health check
        root = client.get(f"{BASE_URL}/")
        _assert_status(root, 200)

        # Auth
        token = _login(client)
        headers = _auth_headers(token)

        me = client.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
        _assert_status(me, 200)
        assert me.json().get("email") == USERNAME

        # Clean state before simulation
        reset_before = client.delete(f"{BASE_URL}/api/v1/ui/data/reset", headers=headers)
        _assert_status(reset_before, 200)
        assert reset_before.json().get("ok") is True

        # Generate realistic dataset
        simulate = client.post(
            f"{BASE_URL}/api/v1/ui/data/simulate",
            headers=headers,
            params={"days": 60, "transactions_per_day": 10},
        )
        _assert_status(simulate, 200)
        simulate_payload = simulate.json()
        assert simulate_payload.get("ok") is True
        assert simulate_payload.get("transactions_created", 0) > 0
        assert simulate_payload.get("analyses_created", 0) > 0
        diagnostics = simulate_payload.get("diagnostics", {})
        assert diagnostics.get("db_write") is True
        assert diagnostics.get("fraud_pipeline") is True
        assert diagnostics.get("carbon_pipeline") is True
        assert diagnostics.get("reporting_pipeline") is True

        # Histories used by frontend
        csv_history_resp = client.get(f"{BASE_URL}/api/v1/analysis/", headers=headers)
        _assert_status(csv_history_resp, 200)
        csv_history = csv_history_resp.json()
        assert isinstance(csv_history, list)
        assert len(csv_history) > 0

        banking_history_resp = client.get(f"{BASE_URL}/api/v1/banking/analysis/history", headers=headers)
        _assert_status(banking_history_resp, 200)
        banking_history = banking_history_resp.json()
        assert isinstance(banking_history, list)
        assert len(banking_history) > 0

        all_analyses = sorted(
            [*csv_history, *banking_history],
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )
        latest = all_analyses[0]
        summary = latest.get("analysis_results", {}).get("summary", {})
        assert summary.get("total_transactions", 0) > 0

        # Transactions filter endpoint used by frontend table
        tx_resp = client.get(
            f"{BASE_URL}/api/v1/ui/transactions",
            headers=headers,
            params={
                "q": "Movimentacao",
                "min_amount": 1,
                "sort_by": "amount",
                "sort_dir": "desc",
                "limit": 50,
            },
        )
        _assert_status(tx_resp, 200)
        tx_rows = tx_resp.json()
        assert isinstance(tx_rows, list)
        assert len(tx_rows) > 0
        assert tx_rows[0].get("id")
        assert "amount" in tx_rows[0]

        # CSV export endpoint
        export_resp = client.get(f"{BASE_URL}/api/v1/ui/transactions/export.csv", headers=headers)
        _assert_status(export_resp, 200)
        assert "text/csv" in export_resp.headers.get("content-type", "")
        assert "id,transaction_date,description,amount,category,source" in export_resp.text

        # UI settings endpoints
        settings_get = client.get(f"{BASE_URL}/api/v1/ui/settings", headers=headers)
        _assert_status(settings_get, 200)
        current_settings = settings_get.json().get("settings", {})
        assert "isolation_forest_threshold" in current_settings

        new_settings = dict(current_settings)
        new_settings["isolation_forest_threshold"] = 0.73
        settings_put = client.put(
            f"{BASE_URL}/api/v1/ui/settings",
            headers=headers,
            json={"settings": new_settings},
        )
        _assert_status(settings_put, 200)
        assert settings_put.json().get("settings", {}).get("isolation_forest_threshold") == 0.73

        # Reports: generate/list/download
        generate_report = client.post(
            f"{BASE_URL}/api/v1/ui/reports/generate",
            headers=headers,
            json={"analysis_id": latest["id"], "report_type": "analysis_summary"},
        )
        _assert_status(generate_report, 200)
        report = generate_report.json()
        report_id = report["id"]

        list_reports = client.get(f"{BASE_URL}/api/v1/ui/reports", headers=headers)
        _assert_status(list_reports, 200)
        reports = list_reports.json()
        assert any(r["id"] == report_id for r in reports)

        download_report = client.get(f"{BASE_URL}/api/v1/ui/reports/{report_id}/download", headers=headers)
        _assert_status(download_report, 200)
        assert "Report Type" in download_report.text
        assert "Analysis ID" in download_report.text

        # Report schedules
        create_schedule = client.post(
            f"{BASE_URL}/api/v1/ui/reports/schedules",
            headers=headers,
            json={
                "report_type": "analysis_summary",
                "frequency": "daily",
                "recipients": "ops@example.com,compliance@example.com",
            },
        )
        _assert_status(create_schedule, 200)
        schedule_id = create_schedule.json()["id"]

        list_schedules = client.get(f"{BASE_URL}/api/v1/ui/reports/schedules", headers=headers)
        _assert_status(list_schedules, 200)
        schedules = list_schedules.json()
        assert any(s["id"] == schedule_id for s in schedules)

        # Audit verification (schema de historico nao expõe blockchain_tx_hash hoje)
        # então validamos o contrato do endpoint com hash inexistente.
        verify_hash = client.post(
            f"{BASE_URL}/api/v1/ui/audit/verify",
            headers=headers,
            json={"hash": f"0x{uuid.uuid4().hex}"},
        )
        _assert_status(verify_hash, 200)
        verify_payload = verify_hash.json()
        assert verify_payload.get("verified") is False
        assert verify_payload.get("analysis_id") is None

        # Clean state after test (keeps reruns deterministic)
        reset_after = client.delete(f"{BASE_URL}/api/v1/ui/data/reset", headers=headers)
        _assert_status(reset_after, 200)
        assert reset_after.json().get("ok") is True
