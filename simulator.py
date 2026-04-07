import pandas as pd
import requests
import time
import random
import sys

# Load datasets
try:
    normal = pd.read_csv("patientMonitoring.csv")
    attack = pd.read_csv("Attack.csv")
    print("Datasets loaded successfully!")
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure CSV files are in the same folder.")
    sys.exit()

URL = "http://127.0.0.1:5000/api/vitals"

print("Starting Medical Traffic Simulator...")
print("Press Ctrl+C to stop.")

while True:
    # 85% chance of Normal, 15% chance of Anomaly for better demo visibility
    if random.random() > 0.15:
        row = normal.sample(1).to_dict('records')[0]
        label_type = "NORMAL"
    else:
        row = attack.sample(1).to_dict('records')[0]
        label_type = "!! ANOMALY !!"

    # Add a mock IP source if it doesn't exist in your CSV for the UI
    if 'ip.src' not in row:
        row['ip.src'] = f"192.168.1.{random.randint(10, 254)}"

    try:
        response = requests.post(URL, json=row, timeout=1)
        if response.status_code == 200:
            res_data = response.json()
            status = "DETECTED" if res_data.get('is_anomaly') else "CLEARED"
            print(f"[{label_type}] {row['ip.src']} | Frame: {row['frame.len']} | System: {status}")
        else:
            print(f"Server Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Error: Backend (app.py) is not running!")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    # Adjusted sleep: 0.8s for a "fast-moving" real-time feel on your dashboard
    time.sleep(0.8)