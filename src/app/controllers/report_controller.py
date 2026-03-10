import csv
import io
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.domains.identity.dependencies import get_current_user
from src.infra.persistence.database import apply_user_rls_context, get_db
from src.infra.persistence.models import (
    FinancialAnalysis,
    GeneratedReport,
    ReportSchedule,
    Transaction,
    User,
    UserUiSetting,
)
from src.infra.shared.schemas.ui_schema import (
    AuditVerifyPayload,
    ReportGeneratePayload,
    ReportItem,
    ReportScheduleCreatePayload,
    ReportScheduleItem,
    UiSettingsPayload,
)

router = APIRouter(prefix="/ui")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "isolation_forest_threshold": 0.70,
    "auto_retrain": True,
    "audit_restricted_mode": False,
}

CATEGORY_FACTORS = {
    "transferencia": 0.08,
    "servicos": 0.03,
    "tecnologia": 0.02,
    "varejo": 0.05,
    "alimentacao": 0.04,
    "cambio": 0.12,
    "imoveis": 0.06,
    "seguros": 0.05,
    "transporte": 0.03,
}


@router.get("/settings")
def get_ui_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    apply_user_rls_context(db, current_user.id)
    settings_row = db.query(UserUiSetting).filter(UserUiSetting.user_id == current_user.id).first()
    if not settings_row:
        settings_row = UserUiSetting(user_id=current_user.id, settings=DEFAULT_SETTINGS.copy())
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return {"settings": settings_row.settings}


@router.put("/settings")
def update_ui_settings(
    payload: UiSettingsPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    apply_user_rls_context(db, current_user.id)
    settings_row = db.query(UserUiSetting).filter(UserUiSetting.user_id == current_user.id).first()
    if not settings_row:
        settings_row = UserUiSetting(user_id=current_user.id, settings=payload.settings)
        db.add(settings_row)
    else:
        settings_row.settings = payload.settings
    db.commit()
    return {"ok": True, "settings": payload.settings}


@router.get("/transactions/export.csv")
def export_transactions_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    apply_user_rls_context(db, current_user.id)
    txs: List[Transaction] = (
        db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.transaction_date.desc()).all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "transaction_date", "description", "amount", "category", "source"])
    for tx in txs:
        writer.writerow([tx.id, tx.transaction_date, tx.description, float(tx.amount), tx.category, tx.source])

    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=transactions_export.csv"
    return response


@router.get("/transactions")
def list_transactions_filtered(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None),
    max_amount: Optional[float] = Query(default=None),
    sort_by: str = Query(default="transaction_date"),
    sort_dir: str = Query(default="desc"),
    limit: int = Query(default=200, ge=1, le=1000),
):
    apply_user_rls_context(db, current_user.id)
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            (Transaction.description.ilike(like_q)) | (Transaction.category.ilike(like_q)) | (Transaction.source.ilike(like_q))
        )
    if category:
        query = query.filter(Transaction.category.ilike(f"%{category}%"))
    if source:
        query = query.filter(Transaction.source.ilike(f"%{source}%"))
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    sort_map = {
        "id": Transaction.id,
        "transaction_date": Transaction.transaction_date,
        "amount": Transaction.amount,
        "category": Transaction.category,
        "source": Transaction.source,
    }
    sort_col = sort_map.get(sort_by, Transaction.transaction_date)
    if sort_dir.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    rows = query.limit(limit).all()
    return [
        {
            "id": f"TX-{tx.id}",
            "timestamp": tx.transaction_date.isoformat() if tx.transaction_date else None,
            "merchant": tx.description,
            "category": tx.category,
            "amount": float(tx.amount),
            "riskScore": 0,
            "status": "approved",
            "auditHash": "",
            "source": tx.source,
        }
        for tx in rows
    ]


@router.get("/reports", response_model=List[ReportItem])
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    apply_user_rls_context(db, current_user.id)
    return (
        db.query(GeneratedReport)
        .filter(GeneratedReport.user_id == current_user.id)
        .order_by(GeneratedReport.created_at.desc())
        .all()
    )


@router.post("/reports/generate", response_model=ReportItem)
def generate_report(
    payload: ReportGeneratePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    apply_user_rls_context(db, current_user.id)

    analysis_query = db.query(FinancialAnalysis).filter(FinancialAnalysis.user_id == current_user.id)
    if payload.analysis_id:
        analysis_query = analysis_query.filter(FinancialAnalysis.id == payload.analysis_id)
    analysis = analysis_query.order_by(FinancialAnalysis.created_at.desc()).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis found for report generation.")

    summary = analysis.analysis_results.get("summary", {})
    fraud = analysis.analysis_results.get("fraud_analysis", {})
    carbon = analysis.analysis_results.get("carbon_analysis", {})

    lines = [
        f"Report Type: {payload.report_type}",
        f"Analysis ID: {analysis.id}",
        f"Generated At: {datetime.utcnow().isoformat()}Z",
        "",
        f"Total Transactions: {summary.get('total_transactions', 0)}",
        f"Total Amount: {summary.get('total_amount', 0)}",
        f"Fraud Detected: {fraud.get('fraud_detected', False)}",
        f"Highest Risk Score: {fraud.get('highest_risk_score', 0)}",
        f"Total Carbon Kg: {carbon.get('total_carbon_kg', 0)}",
    ]

    report = GeneratedReport(
        user_id=current_user.id,
        title=payload.title or f"Report {analysis.id}",
        report_type=payload.report_type,
        content="\n".join(lines),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    apply_user_rls_context(db, current_user.id)
    report = (
        db.query(GeneratedReport)
        .filter(GeneratedReport.id == report_id, GeneratedReport.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return PlainTextResponse(
        report.content,
        headers={"Content-Disposition": f'attachment; filename="report_{report.id}.txt"'},
    )


@router.post("/audit/verify")
def verify_audit_hash(
    payload: AuditVerifyPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    apply_user_rls_context(db, current_user.id)
    found = (
        db.query(FinancialAnalysis)
        .filter(
            FinancialAnalysis.user_id == current_user.id,
            FinancialAnalysis.blockchain_tx_hash == payload.hash,
        )
        .first()
    )
    return {
        "verified": bool(found),
        "hash": payload.hash,
        "analysis_id": found.id if found else None,
    }


@router.get("/reports/schedules", response_model=List[ReportScheduleItem])
def list_report_schedules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    apply_user_rls_context(db, current_user.id)
    return (
        db.query(ReportSchedule)
        .filter(ReportSchedule.user_id == current_user.id, ReportSchedule.active == True)
        .order_by(ReportSchedule.created_at.desc())
        .all()
    )


@router.post("/reports/schedules", response_model=ReportScheduleItem)
def create_report_schedule(
    payload: ReportScheduleCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    apply_user_rls_context(db, current_user.id)
    schedule = ReportSchedule(
        user_id=current_user.id,
        report_type=payload.report_type,
        frequency=payload.frequency,
        recipients=payload.recipients,
        active=True,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post("/data/simulate")
def simulate_backend_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(default=90, ge=7, le=365),
    transactions_per_day: int = Query(default=12, ge=1, le=60),
):
    apply_user_rls_context(db, current_user.id)

    now = datetime.utcnow()
    categories = list(CATEGORY_FACTORS.keys())
    merchants = [
        "B3 S.A.",
        "TOTVS S.A.",
        "Microsoft",
        "AWS Brasil",
        "Google Ads",
        "Kalunga",
        "Uber",
        "iFood",
        "Porto Seguro",
        "WeWork",
    ]
    banks = ["ITAU", "BRADESCO", "SANTANDER", "NUBANK", "INTER", "BTG"]

    created_transactions = 0
    created_analyses = 0
    diagnostics = {
        "db_write": False,
        "fraud_pipeline": False,
        "carbon_pipeline": False,
        "reporting_pipeline": False,
    }

    all_generated = []
    for day_offset in range(days):
        tx_date = (now - timedelta(days=day_offset)).date()
        for _ in range(transactions_per_day):
            category = random.choice(categories)
            base_amount = random.uniform(20.0, 250000.0)
            signed_amount = base_amount if random.random() > 0.35 else -base_amount
            tx = Transaction(
                description=f"Movimentacao {random.choice(merchants)}",
                amount=round(signed_amount, 2),
                category=category,
                transaction_date=tx_date,
                user_id=current_user.id,
                source=f"{random.choice(banks)}_SYNC",
            )
            db.add(tx)
            all_generated.append(tx)
            created_transactions += 1

    db.flush()
    diagnostics["db_write"] = True

    window = max(1, days // 12)
    for i in range(0, len(all_generated), window * transactions_per_day):
        chunk = all_generated[i : i + (window * transactions_per_day)]
        if not chunk:
            continue

        total_amount = float(sum(float(t.amount) for t in chunk))
        total_transactions = len(chunk)

        highest_risk_score = 0.0
        flagged = 0
        carbon_total = 0.0
        breakdown: Dict[str, float] = {}
        riskiest = []
        for t in chunk:
            factor = CATEGORY_FACTORS.get(t.category, 0.03)
            risk = min(0.99, abs(float(t.amount)) / 1_000_000 + factor + random.uniform(0.0, 0.2))
            carbon = abs(float(t.amount)) * (factor / 10.0)
            carbon_total += carbon
            breakdown[t.category] = breakdown.get(t.category, 0.0) + carbon
            if risk > highest_risk_score:
                highest_risk_score = risk
            if risk > 0.7:
                flagged += 1
                riskiest.append(
                    {
                        "id": f"TX-{t.id}",
                        "amount": float(t.amount),
                        "category": t.category,
                        "transaction_date": t.transaction_date.isoformat(),
                        "risk_score": risk,
                    }
                )

        diagnostics["fraud_pipeline"] = True
        diagnostics["carbon_pipeline"] = True

        analysis_results = {
            "summary": {
                "total_transactions": total_transactions,
                "total_amount": round(total_amount, 2),
            },
            "fraud_analysis": {
                "fraud_detected": flagged > 0,
                "highest_risk_score": round(highest_risk_score, 4),
                "transactions_above_threshold": flagged,
                "riskiest_transactions": sorted(riskiest, key=lambda x: x["risk_score"], reverse=True)[:25],
                "model_version": "ensemble_sim_v1",
            },
            "carbon_analysis": {
                "total_carbon_kg": round(carbon_total, 4),
                "breakdown_by_category": {k: round(v, 4) for k, v in breakdown.items()},
            },
            "legacy_processing": {
                "processed_transactions": total_transactions,
                "total_amount": round(total_amount, 2),
                "invalid_transactions": 0,
                "processing_mode": "simulation",
            },
            "generative_summary": "Simulation dataset generated for UI and backend validation.",
        }

        analysis = FinancialAnalysis(
            analysis_results=analysis_results,
            user_id=current_user.id,
            blockchain_tx_hash=f"0x{uuid.uuid4().hex}",
            analysis_type="BANKING" if created_analyses % 2 else "CSV",
        )
        db.add(analysis)
        created_analyses += 1

    if not db.query(UserUiSetting).filter(UserUiSetting.user_id == current_user.id).first():
        db.add(UserUiSetting(user_id=current_user.id, settings=DEFAULT_SETTINGS.copy()))

    db.add(
        GeneratedReport(
            user_id=current_user.id,
            title="Relatorio de Simulacao Inicial",
            report_type="analysis_summary",
            content="Dataset sintetico gerado com sucesso para validacao de frontend e backend.",
        )
    )
    db.add(
        ReportSchedule(
            user_id=current_user.id,
            report_type="analysis_summary",
            frequency="daily",
            recipients=current_user.email,
            active=True,
        )
    )
    diagnostics["reporting_pipeline"] = True
    db.commit()

    return {
        "ok": True,
        "transactions_created": created_transactions,
        "analyses_created": created_analyses,
        "diagnostics": diagnostics,
        "message": "Simulacao concluida e dados preenchidos.",
    }


@router.delete("/data/reset")
def reset_user_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    apply_user_rls_context(db, current_user.id)

    db.execute(delete(ReportSchedule).where(ReportSchedule.user_id == current_user.id))
    db.execute(delete(GeneratedReport).where(GeneratedReport.user_id == current_user.id))
    db.execute(delete(FinancialAnalysis).where(FinancialAnalysis.user_id == current_user.id))
    db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))
    db.execute(delete(UserUiSetting).where(UserUiSetting.user_id == current_user.id))
    db.commit()
    return {"ok": True, "message": "Dados do usuario removidos."}
