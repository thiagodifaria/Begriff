
import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

# Ensure the models directory exists
os.makedirs("src/domains/risk/models", exist_ok=True)

# Create a simple dummy dataset
X = np.random.rand(100, 2)
y = np.random.randint(0, 2, 100)

# Train a LogisticRegression model
model = LogisticRegression()
model.fit(X, y)

# Save the trained model
joblib.dump(model, "src/domains/risk/models/fraud_model_v1.pkl")

print("Mock model created successfully at src/domains/risk/models/fraud_model_v1.pkl")
