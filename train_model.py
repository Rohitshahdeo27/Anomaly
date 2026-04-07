import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# 1. Load Normal Datasets
patient = pd.read_csv("patientMonitoring.csv")
env = pd.read_csv("environmentMonitoring.csv")
train_df = pd.concat([patient, env])

# 2. Select Behavioral Features (Avoid IDs and IPs)
features = [
    'frame.len', 'tcp.len', 'tcp.time_delta', 'tcp.window_size_value',
    'mqtt.len', 'mqtt.msgtype', 'mqtt.qos', 'ip.ttl'
]

# 3. Clean and Scale
X = train_df[features].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Train Isolation Forest
# contamination is set low because this is our 'clean' baseline
model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
model.fit(X_scaled)

# 5. Save Model and Scaler
joblib.dump(model, 'iso_forest_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
print("Model training complete. Files saved: iso_forest_model.pkl, scaler.pkl")