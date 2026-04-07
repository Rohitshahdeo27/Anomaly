from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import io
import csv
import os
from datetime import datetime
import pytz

app = Flask(__name__)
# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def get_ist():
    return datetime.now(pytz.timezone('Asia/Kolkata'))
# --- DATABASE MODEL ---
class TrafficLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=get_ist)
    frame_len = db.Column(db.Float)
    tcp_len = db.Column(db.Float)
    ip_source = db.Column(db.String(50))
    is_anomaly = db.Column(db.Boolean)
    anomaly_score = db.Column(db.Float)

# Initialize database
with app.app_context():
    db.create_all()

# --- LOAD AI MODELS ---
model = joblib.load('iso_forest_model.pkl')
scaler = joblib.load('scaler.pkl')
features = ['frame.len', 'tcp.len', 'tcp.time_delta', 'tcp.window_size_value', 'mqtt.len', 'mqtt.msgtype', 'mqtt.qos', 'ip.ttl']

# --- PAGE ROUTING ---

@app.route('/')
def index():
    """Live Dashboard Page"""
    return render_template('index.html', active_page='dashboard')

@app.route('/history')
def history():
    """Historical Logs Page"""
    # Fetch all logs to display in a large table
    all_logs = TrafficLog.query.order_by(TrafficLog.timestamp.desc()).all()
    return render_template('history.html', logs=all_logs, active_page='history')

@app.route('/settings')
def settings():
    """System Management Page"""
    log_count = TrafficLog.query.count()
    return render_template('settings.html', log_count=log_count, active_page='settings')

# --- API ENDPOINTS ---

@app.route('/api/vitals', methods=['POST'])
def process_vitals():
    data = request.json
    input_data = [data.get(f, 0) for f in features]
    
    # Use DataFrame to avoid feature name warnings
    input_df = pd.DataFrame([input_data], columns=features)
    scaled_input = scaler.transform(input_df)
    
    prediction = model.predict(scaled_input)[0]
    score = model.decision_function(scaled_input)[0] 
    is_anomaly = True if prediction == -1 else False
    
    # Save to Database
    new_log = TrafficLog(
        frame_len=float(data.get('frame.len', 0)),
        tcp_len=float(data.get('tcp.len', 0)),
        ip_source=data.get('ip.src', '192.168.1.1'),
        is_anomaly=is_anomaly,
        anomaly_score=float(score)
    )
    db.session.add(new_log)
    db.session.commit()
    
    # Live Update
    socketio.emit('update_dashboard', {
        'vitals': data,
        'is_anomaly': is_anomaly,
        'score': round(score, 4),
        'time': get_ist().strftime("%H:%M:%S")
    })
    return {"status": "success"}

@app.route('/api/export')
def export_logs():
    logs = TrafficLog.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Source IP', 'Frame Len', 'Anomaly', 'Score'])
    for log in logs:
        writer.writerow([log.timestamp, log.ip_source, log.frame_len, log.is_anomaly, log.anomaly_score])
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='security_report.csv')

@app.route('/api/clear', methods=['POST'])
def clear_logs():
    db.session.query(TrafficLog).delete()
    db.session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    socketio.run(app, debug=True)