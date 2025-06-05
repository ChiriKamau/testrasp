import serial
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
from datetime import datetime

# Setup Firebase Admin
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://espcam-69f58-default-rtdb.firebaseio.com'
})

def setup_serial():
    ports_to_try = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    for port in ports_to_try:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)
            print(f"Connected to {port}")
            return ser
        except serial.SerialException:
            continue
    
    raise Exception("Could not connect to any serial port")

def validate_sensor_data(data):
    required_fields = ['temperature', 'humidity', 'soilMoisture1', 'soilMoisture2', 'soilMoisture3']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    
    if not (-40 <= data['temperature'] <= 80):
        return False, "Temperature out of range"
    
    if not (0 <= data['humidity'] <= 100):
        return False, "Humidity out of range"
    
    return True, "Valid"

def push_to_firebase(data):
    try:
        ref = db.reference('/lima/sensor_readings')
        timestamp = int(time.time())
        
        data['timestamp'] = datetime.now().isoformat()
        data['unix_timestamp'] = timestamp
        
        ref.child(str(timestamp)).set(data)
        print(f"✓ Pushed data: {data}")
        return True
    except Exception as e:
        print(f"✗ Firebase error: {e}")
        return False

# Main loop with reconnection logic
while True:
    try:
        ser = setup_serial()
        print("Starting data collection...")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        sensor_data = json.loads(line)
                        
                        # Validate data
                        is_valid, message = validate_sensor_data(sensor_data)
                        if is_valid:
                            push_to_firebase(sensor_data)
                        else:
                            print(f"Invalid data: {message} - {sensor_data}")
                            
                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {line}")
            
            time.sleep(1)
            
    except serial.SerialException as e:
        print(f"Serial connection lost: {e}")
        print("Attempting to reconnect in 5 seconds...")
        time.sleep(5)
    except KeyboardInterrupt:
        print("Program terminated by user")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(5)