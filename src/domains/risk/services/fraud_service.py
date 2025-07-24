import joblib
import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Load the Isolation Forest model
_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'fraud_model_v1.pkl')
_model = joblib.load(_model_path)

async def analyze_for_fraud(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes a list of financial transactions for fraudulent activity using an Isolation Forest model.
    """
    if not transactions:
        return {
            "fraud_detected": False,
            "highest_risk_score": 0.0,
            "transactions_above_threshold": 0,
            "riskiest_transactions": []
        }

    # 1. Perform Feature Engineering: Convert transactions to DataFrame and create features
    df = pd.DataFrame(transactions)

    # Ensure 'amount' is numeric. Handle potential non-numeric values by coercing to numeric.
    # Errors will turn non-parseable values into NaN, which we can then fill or drop.
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

    # For 'time_of_day', assuming 'timestamp' exists and is in a format convertible to datetime.
    # If 'timestamp' is not present or is not a datetime-like string/number, 
    # you might need to adjust this or use a placeholder.
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['time_of_day'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60
    else:
        # Placeholder if no timestamp is available. Adjust based on actual data.
        df['time_of_day'] = np.random.rand(len(df)) * 24 # Random hour for dummy data

    # Select features that the model was trained on. 
    # Ensure these match the features used in create_mock_model.py (amount, time_of_day).
    # Drop rows with NaN values that resulted from coercion or missing data.
    X = df[['amount', 'time_of_day']].dropna()

    # If, after dropping NaNs, X is empty, return early.
    if X.empty:
        return {
            "fraud_detected": False,
            "highest_risk_score": 0.0,
            "transactions_above_threshold": 0,
            "riskiest_transactions": []
        }

    # 2. Use the Correct Prediction Method: _model.score_samples(X)
    # Lower values are more anomalous.
    anomaly_scores = _model.score_samples(X)

    # 3. Normalize the Scores: Invert and normalize to a 0-1 risk scale
    # Higher score = higher risk
    min_score = anomaly_scores.min()
    max_score = anomaly_scores.max()

    if (max_score - min_score) == 0:
        # Avoid division by zero if all scores are identical
        risk_scores = np.zeros_like(anomaly_scores)
    else:
        # Invert and normalize: most anomalous (lowest score) becomes ~1.0, least anomalous (highest score) becomes ~0.0
        risk_scores = 1 - (anomaly_scores - min_score) / (max_score - min_score)

    # Add risk scores back to the DataFrame for easier processing
    # Align scores back to original transactions, handling dropped NaNs
    df_with_scores = df.loc[X.index].copy() # Use .loc with X.index to align
    df_with_scores['risk_score'] = risk_scores

    # 4. Process and Return Results
    highest_risk_score = df_with_scores['risk_score'].max() if not df_with_scores.empty else 0.0

    # Define a high-risk threshold
    high_risk_threshold = 0.85
    transactions_above_threshold = (df_with_scores['risk_score'] > high_risk_threshold).sum()

    # Identify the riskiest transactions (e.g., top 3 or all above threshold)
    riskiest_transactions_df = df_with_scores[df_with_scores['risk_score'] > high_risk_threshold].sort_values(by='risk_score', ascending=False)
    
    # Convert to list of dicts, including original transaction data and risk_score
    riskiest_transactions = riskiest_transactions_df.to_dict(orient='records')

    fraud_detected = highest_risk_score > high_risk_threshold # Simple detection based on highest score

    return {
        "fraud_detected": fraud_detected,
        "highest_risk_score": float(highest_risk_score),
        "transactions_above_threshold": int(transactions_above_threshold),
        "riskiest_transactions": riskiest_transactions
    }