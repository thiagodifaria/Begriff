import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

# Define the path to save the model
model_path = "src/domains/risk/models/fraud_model_v1.pkl"

# 1. Create a more realistic dummy dataset for anomaly detection
# Generate "normal" data points (e.g., amount, time_of_day)
np.random.seed(42)
num_normal = 1000
normal_data = np.random.randn(num_normal, 2) * np.array([50, 2]) + np.array([100, 12])

# Generate "outlier" data points
num_outliers = 20
outlier_data_1 = np.random.randn(num_outliers // 2, 2) * np.array([1000, 5]) + np.array([5000, 2])
outlier_data_2 = np.random.randn(num_outliers // 2, 2) * np.array([10, 1]) + np.array([10, 23])

X = np.concatenate((normal_data, outlier_data_1, outlier_data_2), axis=0)

# Ensure the model directory exists
os.makedirs(os.path.dirname(model_path), exist_ok=True)

# 2. Instantiate IsolationForest
# contamination='auto' tries to estimate the proportion of outliers in the data.
# random_state for reproducibility.
model = IsolationForest(contamination='auto', random_state=42)

# 3. Fit the model to the new dataset
model.fit(X)

# 4. Save the newly trained IsolationForest model
joblib.dump(model, model_path)

print(f"Isolation Forest model trained and saved to {model_path}")