import joblib
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from typing import Dict, Any, List

_model_path = os.path.join(os.path.dirname(__file__), '..', 'models')
_model_path = os.path.abspath(os.path.join("/app", "domains/risk/models"))
_if_model = joblib.load(os.path.join(_model_path, 'fraud_model_v1.pkl'))
_scaler = joblib.load(os.path.join(_model_path, 'scaler.pkl'))
_autoencoder = tf.keras.models.load_model(os.path.join(_model_path, 'autoencoder_v1.keras'))

async def analyze_for_fraud(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes a list of financial transactions for fraudulent activity using an ensemble of
    Isolation Forest and an Autoencoder.
    """
    if not transactions:
        return {
            "fraud_detected": False,
            "highest_risk_score": 0.0,
            "transactions_above_threshold": 0,
            "riskiest_transactions": [],
            "model_version": "ensemble_v1"
        }

    df = pd.DataFrame(transactions)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    timestamp_col = None
    for col in ['timestamp', 'transaction_date', 'date', 'created_at']:
        if col in df.columns:
            timestamp_col = col
            break
    
    if timestamp_col:
        try:
            df['time_of_day'] = pd.to_datetime(df[timestamp_col], errors='coerce').dt.hour
        except:
            df['time_of_day'] = 12
    else:
        df['time_of_day'] = 12
    
    df['time_of_day'] = df['time_of_day'].fillna(12)
    df = df.dropna(subset=['amount'])

    if df.empty:
        return {
            "fraud_detected": False,
            "highest_risk_score": 0.0,
            "transactions_above_threshold": 0,
            "riskiest_transactions": [],
            "model_version": "ensemble_v1",
            "warning": "No valid transactions after data cleaning"
        }

    X = df[['amount', 'time_of_day']]

    X_scaled = _scaler.transform(X)

    if_scores = _if_model.score_samples(X_scaled)
    if_risk_scores = 1 - (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min())

    reconstructed_data = _autoencoder.predict(X_scaled, verbose=0)
    mse = np.mean(np.power(X_scaled - reconstructed_data, 2), axis=1)
    ae_risk_scores = (mse - mse.min()) / (mse.max() - mse.min())

    final_risk_scores = (if_risk_scores * 0.5) + (ae_risk_scores * 0.5)

    df['risk_score'] = final_risk_scores
    high_risk_threshold = 0.7
    riskiest_transactions = df[df['risk_score'] > high_risk_threshold].sort_values(by='risk_score', ascending=False)

    return {
        "fraud_detected": any(df['risk_score'] > high_risk_threshold),
        "highest_risk_score": float(df['risk_score'].max()),
        "transactions_above_threshold": len(riskiest_transactions),
        "riskiest_transactions": riskiest_transactions.to_dict(orient='records'),
        "model_version": "ensemble_v1",
        "timestamp_column_used": timestamp_col or "none (default hour used)"
    }