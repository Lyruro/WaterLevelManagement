import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from time import sleep, time
import json
import csv
from datetime import datetime

# MQTT Configuration - WITH YOUR HIVEMQ CREDENTIALS
MQTT_BROKER = "36b320a09b064246a35d373ba69a5735.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "water-tank/group5/monitor"  # Made topic unique to your group
MQTT_USERNAME = "group5"
MQTT_PASSWORD = "shmG143imbf@"

# GPIO Configuration
GPIO.setmode(GPIO.BCM)
TRIGGER_PIN = 23
ECHO_PIN = 24
RELAY_PIN = 17

# Setup GPIO pins
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Initialize pins
GPIO.output(TRIGGER_PIN, False)
GPIO.output(RELAY_PIN, False)  # Relay OFF initially

# Track pump state and metrics
pump_is_on = False
total_pump_time = 0
pump_start_time = None
session_start_time = time()

def get_distance():
    """Get distance measurement from ultrasonic sensor in cm"""
    # Send trigger pulse
    GPIO.output(TRIGGER_PIN, True)
    sleep(0.00001)
    GPIO.output(TRIGGER_PIN, False)

    # Wait for echo response
    pulse_start = time()
    timeout = pulse_start + 0.1  # 100ms timeout
    
    while GPIO.input(ECHO_PIN) == 0 and pulse_start < timeout:
        pulse_start = time()
    
    if pulse_start >= timeout:
        return None

    pulse_end = time()
    while GPIO.input(ECHO_PIN) == 1 and pulse_end < timeout:
        pulse_end = time()
    
    if pulse_end >= timeout:
        return None

    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # Speed of sound in cm/s
    
    return distance

def calculate_water_level(distance_cm):
    """Convert distance to water level percentage"""
    tank_height_cm = 17  # Adjust this to your actual tank height
    water_level = max(0, min(100, ((tank_height_cm - distance_cm) / tank_height_cm) * 100))
    return round(water_level, 1)

def calculate_volume(water_level_percent):
    """Calculate water volume based on level percentage"""
    tank_capacity_liters = 2  # Adjust this to your actual tank capacity
    return round((water_level_percent / 100) * tank_capacity_liters, 1)

def on_connect(client, userdata, flags, rc):
    """Callback for when client connects to MQTT broker"""
    if rc == 0:
        print("✅ Successfully connected to HiveMQ broker")
    else:
        print(f"❌ Failed to connect to HiveMQ, return code: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback for when client disconnects from MQTT broker"""
    print("⚠️  Disconnected from HiveMQ broker")

# MQTT client setup with authentication
client = mqtt.Client()

# Set authentication
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Enable TLS (important for HiveMQ Cloud)
client.tls_set()  # Use default certificates

# Optional: disable hostname check if you have issues (not recommended for production)
# client.tls_insecure_set(True)

# Attach callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect

try:
    print("🔌 Connecting to HiveMQ...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    # Wait for connection
    sleep(2)
    
    print("🚀 Starting Water Tank Monitoring with MQTT (RPi.GPIO)...")
    sleep(1)  # Allow sensor to settle
    
    while True:
        # Get distance measurement
        distance_cm = get_distance()
        
        if distance_cm is None:
            print("❌ Error: Failed to get distance measurement")
            sleep(1)
            continue

        # Calculate derived metrics
        water_level = calculate_water_level(distance_cm)
        current_volume = calculate_volume(water_level)
        
        # Update pump runtime tracking
        if pump_is_on:
            if pump_start_time is not None:
                total_pump_time += time() - pump_start_time
                pump_start_time = time()
        else:
            pump_start_time = None

        # Pump control logic
        if distance_cm >= 17 and not pump_is_on:  # Low water level
            print(f"💧 Distance {distance_cm:.1f} cm >= 17 cm → Turning pump ON.")
            GPIO.output(RELAY_PIN, True)  # Relay ON
            pump_is_on = True
            pump_start_time = time()

        elif distance_cm <= 5 and pump_is_on:  # High water level
            print(f"💧 Distance {distance_cm:.1f} cm <= 12 cm → Turning pump OFF.")
            GPIO.output(RELAY_PIN, False)  # Relay OFF
            pump_is_on = False
            if pump_start_time:
                total_pump_time += time() - pump_start_time
                pump_start_time = None

        # Prepare data payload
        tank_data = {
            "timestamp": time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "distance_cm": round(distance_cm, 1),
            "water_level_percent": water_level,
            "current_volume_liters": current_volume,
            "pump_status": "ON" if pump_is_on else "OFF",
            "pump_runtime_seconds": round(total_pump_time, 1),
            "session_duration": round(time() - session_start_time, 1)
        }

        # Log tank_data to CSV
        try:
            with open("tank_data.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    tank_data["timestamp"],
                    tank_data["datetime"],
                    tank_data["distance_cm"],
                    tank_data["water_level_percent"],
                    tank_data["current_volume_liters"],
                    tank_data["pump_status"],
                    tank_data["pump_runtime_seconds"]
                ])
        except Exception as e:
            print(f"⚠️  Failed to log to CSV: {e}")

        # Publish to MQTT
        result = client.publish(MQTT_TOPIC, json.dumps(tank_data))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📤 Published: {tank_data}")
        else:
            print(f"❌ Failed to publish message")

        sleep(2)  # Publish every 2 seconds

except KeyboardInterrupt:
    print("🛑 Measurement stopped by user.")
    GPIO.output(RELAY_PIN, False)  # Ensure relay is OFF
    client.loop_stop()
    client.disconnect()
    GPIO.cleanup()
    print("✅ Cleanup completed")
except Exception as e:
    print(f"💥 Error occurred: {e}")
    GPIO.output(RELAY_PIN, False)
    client.loop_stop()
    client.disconnect()
    GPIO.cleanup()