from flask import Flask, render_template, jsonify, send_from_directory
import paho.mqtt.client as mqtt
import json
import csv
import pandas as pd
from datetime import datetime
import os
import threading
import ssl

app = Flask(__name__)

# MQTT Configuration - HiveMQ Cloud with SSL
MQTT_BROKER = "36b320a09b064246a35d373ba69a5735.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "water-tank/group5/monitor"
MQTT_USERNAME = "group5"
MQTT_PASSWORD = "shmG143imbf@"

# CSV file for data storage
CSV_FILE = "tank_data.csv"

# Global variables to store latest data
latest_data = {
    "timestamp": 0,
    "distance_cm": 0,
    "water_level_percent": 0,
    "current_volume_liters": 0,
    "pump_status": "OFF",
    "pump_runtime_seconds": 0,
    "session_duration": 0
}

# Track MQTT connection status
mqtt_connected = False
message_count = 0

# Initialize CSV file with headers if it doesn't exist
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'timestamp', 'datetime', 'distance_cm', 'water_level_percent',
                'current_volume_liters', 'pump_status', 'pump_runtime_seconds'
            ])
        print("✅ CSV file initialized")

# MQTT message callback
def on_message(client, userdata, message):
    global latest_data, message_count
    try:
        data = json.loads(message.payload.decode())
        message_count += 1
        
        print(f"📨 MQTT Message #{message_count} received:")
        print(f"   Topic: {message.topic}")
        print(f"   Data: {data}")
        
        # Update latest data
        latest_data.update(data)
        latest_data['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log to CSV
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                data['timestamp'],
                latest_data['datetime'],
                data['distance_cm'],
                data['water_level_percent'],
                data['current_volume_liters'],
                data['pump_status'],
                data['pump_runtime_seconds']
            ])
        
        print(f"✅ Data logged: {data['water_level_percent']}%")
        print(f"📊 Current latest_data: {latest_data}")
        
    except Exception as e:
        print(f"❌ Error processing MQTT message: {e}")

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print("✅ Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"✅ Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("⚠️  Disconnected from MQTT Broker")

# MQTT setup and connection with SSL
def setup_mqtt():
    try:
        client = mqtt.Client()
        
        # Set username and password
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Configure SSL/TLS
        client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        
        # Set callbacks
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        
        # Connect
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        return client
        
    except Exception as e:
        print(f"❌ MQTT connection failed: {e}")
        return None

# Flask routes
@app.route('/')
def dashboard():
    print("🏠 Serving dashboard page")
    return render_template('dashboard.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/current-data')
def get_current_data():
    print(f"📡 API: Serving current data - MQTT Connected: {mqtt_connected}")
    print(f"📊 Current data being served: {latest_data}")
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    try:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            # Get last 50 records for chart
            recent_data = df.tail(50)
            return jsonify({
                'timestamps': recent_data['datetime'].tolist(),
                'levels': recent_data['water_level_percent'].tolist(),
                'volumes': recent_data['current_volume_liters'].tolist()
            })
        else:
            return jsonify({'timestamps': [], 'levels': [], 'volumes': []})
    except Exception as e:
        print(f"❌ History error: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/stats')
def get_stats():
    try:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if len(df) > 0:
                stats = {
                    'max_level': float(df['water_level_percent'].max()),
                    'min_level': float(df['water_level_percent'].min()),
                    'avg_level': float(df['water_level_percent'].mean()),
                    'total_records': len(df)
                }
                return jsonify(stats)
        return jsonify({})
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return jsonify({'error': str(e)})

@app.route('/debug')
def debug():
    """Debug page to check MQTT status"""
    return f'''
    <h1>Debug Information</h1>
    <p>MQTT Connected: <strong>{mqtt_connected}</strong></p>
    <p>Messages Received: <strong>{message_count}</strong></p>
    <p>Latest Data: <pre>{json.dumps(latest_data, indent=2)}</pre></p>
    <p><a href="/api/current-data">API Data</a></p>
    <p><a href="/">Dashboard</a></p>
    '''

if __name__ == '__main__':
    print("🚀 Starting AquaFlow Dashboard...")
    init_csv()
    
    # Try to setup MQTT
    mqtt_client = setup_mqtt()
    if mqtt_client:
        print("✅ MQTT setup complete")
    else:
        print("⚠️  MQTT not connected - running in demo mode")
    
    print("🌐 Starting Flask server on http://0.0.0.0:5000")
    print("🔍 Visit http://127.0.0.1:5000/debug for MQTT status")
    app.run(host='0.0.0.0', port=5000, debug=True)