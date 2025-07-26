import ray
import joblib
import pandas as pd
from typing import List, Dict, Any

@ray.remote
class EdgeComputeNode:
    """
    A Ray actor that simulates a remote edge compute node.
    """
    def __init__(self, region: str):
        """
        Initializes the edge node and loads the 'lite' ML model.
        """
        self.region = region
        self.fraud_model = joblib.load('/app/src/domains/risk/models/fraud_model_v1.pkl')

    def preprocess_transactions(self, transactions: List[Dict[str, Any]]) -> dict:
        """
        Performs a preliminary analysis on a list of transactions.
        """
        if not transactions:
            return {
                "pre_analysis_risk_score": 0.0,
                "transaction_count": 0,
                "processed_by_node": self.region,
                "error": "No transactions to process"
            }

        # Convert to DataFrame for processing
        df = pd.DataFrame(transactions)

        # Basic data validation and cleaning
        if 'value' not in df.columns:
            return {
                "pre_analysis_risk_score": 0.0,
                "transaction_count": len(transactions),
                "processed_by_node": self.region,
                "error": "Missing 'value' column in transaction data"
            }
        
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df.dropna(subset=['value'], inplace=True)

        if df.empty:
            return {
                "pre_analysis_risk_score": 0.0,
                "transaction_count": len(transactions),
                "processed_by_node": self.region,
                "error": "No valid transactions after cleaning"
            }

        # Predict anomaly score
        # Note: This is a simplified version of the logic in fraud_service.py
        # and might need adjustments based on the actual model's expected input.
        try:
            # Assuming the model expects a DataFrame with a 'value' column
            # and returns a single anomaly score.
            # The actual prediction logic might be more complex.
            # For this example, we'll use a placeholder for the prediction.
            # In a real scenario, you would use self.fraud_model.predict(df)
            # and then calculate the risk score.
            # For now, we'll simulate a risk score.
            risk_score = self.fraud_model.predict(df[['value']]).mean()
        except Exception as e:
            return {
                "pre_analysis_risk_score": 0.0,
                "transaction_count": len(transactions),
                "processed_by_node": self.region,
                "error": str(e)
            }

        return {
            "pre_analysis_risk_score": float(risk_score),
            "transaction_count": len(transactions),
            "processed_by_node": self.region
        }