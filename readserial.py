import serial
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time

# Setup Firebase Admin
cred = credentials.Certificate('firebase-adminsdk.json ')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://espcam-69f58-default-rtdb.firebaseio.com'
})

# Setup serial port (adjust if needed)
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # Wait for serial to initialize

def push_to_firebase(data):
    try:
        ref = db.reference('/lima/sensor_readings')
        # Push data with timestamp as key
        timestamp = int(time.time())
        ref.child(str(timestamp)).set(data)
        print(f"Pushed data at {timestamp}: {data}")
    except Exception as e:
        print(f"Firebase error: {e}")

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                sensor_data = json.loads(line)
                push_to_firebase(sensor_data)
            except json.JSONDecodeError:
                print(f"Invalid JSON: {line}")
    time.sleep(1)
