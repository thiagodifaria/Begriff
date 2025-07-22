
import joblib
import pandas as pd
from typing import List, Dict, Any

# Load the model at module level
_model = joblib.load("src/domains/risk/models/fraud_model_v1.pkl")

def analyze_for_fraud(transactions: List[Dict[str, Any]]) -> dict:
    """
    Analyzes a list of transactions for fraud using a pre-trained model.

    Args:
        transactions: A list of transaction dictionaries.

    Returns:
        A dictionary containing the fraud analysis results.
    """
    if not transactions:
        return {
            "overall_risk_score": 0.0,
            "alerts_found": 0,
            "model_version": "1.0.0"
        }

    df = pd.DataFrame(transactions)

    # Simple feature engineering
    if 'amount' not in df.columns:
        # Handle case where 'amount' is missing
        return {
            "error": "'amount' column not found in transaction data.",
            "overall_risk_score": 0.0,
            "alerts_found": 0,
            "model_version": "1.0.0"
        }

    df['amount'] = pd.to_numeric(df['amount'])
    df['placeholder_feature'] = df['amount'] * 0.1
    X = df[['amount', 'placeholder_feature']]

    # Predict fraud probabilities
    probabilities = _model.predict_proba(X)[:, 1]

    # Process the results
    max_probability = float(probabilities.max())
    alert_count = int((probabilities > 0.75).sum())

    return {
        "overall_risk_score": max_probability,
        "alerts_found": alert_count,
        "model_version": "1.0.0"
    }
