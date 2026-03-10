import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from sklearn.neural_network import MLPRegressor

# Define paths
model_dir = "src/domains/risk/models"
if_model_path = os.path.join(model_dir, "fraud_model_v1.pkl")
scaler_path = os.path.join(model_dir, "scaler.pkl")
autoencoder_path = os.path.join(model_dir, "autoencoder_v1.keras")

# Ensure the model directory exists
os.makedirs(model_dir, exist_ok=True)

# 1. Create a more realistic dummy dataset
np.random.seed(42)
num_normal = 1000
normal_data = np.random.randn(num_normal, 2) * np.array([50, 2]) + np.array([100, 12])

num_outliers = 20
outlier_data_1 = np.random.randn(num_outliers // 2, 2) * np.array([1000, 5]) + np.array([5000, 2])
outlier_data_2 = np.random.randn(num_outliers // 2, 2) * np.array([10, 1]) + np.array([10, 23])

X = np.concatenate((normal_data, outlier_data_1, outlier_data_2), axis=0)
X_normal = normal_data  # Use only normal data for autoencoder training

# 2. Isolation Forest
print("Training Isolation Forest...")
if_model = IsolationForest(contamination='auto', random_state=42)
if_model.fit(X)
joblib.dump(if_model, if_model_path)
print(f"Isolation Forest model saved to {if_model_path}")

# 3. Data Scaler
print("Fitting and saving data scaler...")
scaler = StandardScaler()
scaler.fit(X)
joblib.dump(scaler, scaler_path)
print(f"Scaler saved to {scaler_path}")

# 4. Scikit-learn Autoencoder (using MLPRegressor)
print("Training Autoencoder...")
# Define the autoencoder architecture
autoencoder = MLPRegressor(hidden_layer_sizes=(1,),  # Single hidden layer with 1 neuron (encoding dimension)
                           activation='relu',
                           solver='adam',
                           max_iter=500,
                           shuffle=True,
                           random_state=42,
                           verbose=False)

# Train the autoencoder on scaled normal data
X_normal_scaled = scaler.transform(X_normal)
autoencoder.fit(X_normal_scaled, X_normal_scaled)

# Save the autoencoder
joblib.dump(autoencoder, autoencoder_path)
print(f"Autoencoder model saved to {autoencoder_path}")

print("\nAll models and scaler have been created and saved successfully.")