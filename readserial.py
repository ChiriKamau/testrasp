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
    """Setup serial connection with retry logic"""
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

def get_user_uid():
    """Get the user UID from Firebase (matching your ESP32 approach)"""
    # You'll need to replace this with your actual UID
    # You can get this from your Firebase console or from the ESP32 logs
    return "your_user_uid_here"  # Replace with actual UID

def get_formatted_timestamp():
    """Generate timestamp in the exact same format as your ESP32 code using Raspberry Pi local time"""
    # Get current local time from Raspberry Pi
    current_time = datetime.now()
    
    # Format time as HH:MM:SS
    formatted_time = current_time.strftime("%H:%M:%S")
    
    # Format date and combine exactly like ESP32 code
    year = current_time.year
    month = current_time.month
    day = current_time.day
    
    # Format: YYYY-M-D--HH:MM:SS (exactly matching your ESP32 format)
    current_date_time = f"{year}-{month}-{day}--{formatted_time}"
    
    return current_date_time

def validate_sensor_data(data):
    """Validate sensor data before pushing to Firebase"""
    required_fields = ['temperature', 'humidity', 'soilMoisture1', 'soilMoisture2', 'soilMoisture3']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    
    # Check for reasonable ranges
    if not (-40 <= data['temperature'] <= 80):
        return False, "Temperature out of range"
    
    if not (0 <= data['humidity'] <= 100):
        return False, "Humidity out of range"
    
    return True, "Valid"

def push_to_firebase(data, uid):
    """Push sensor data to Firebase in the exact same format as ESP32"""
    try:
        # Get formatted timestamp matching ESP32 format
        current_date_time = get_formatted_timestamp()
        
        # Create database path exactly like ESP32: /lima/{uid}/readings/{timestamp}
        database_path = f"/lima/{uid}/readings"
        parent_path = f"{database_path}/{current_date_time}"
        
        # Create the data structure matching ESP32 format
        firebase_data = {
            "/temperature": str(data['temperature']),
            "/humidity": str(data['humidity']),
            "/SoilMoisture1": str(data['soilMoisture1']),
            "/SoilMoisture2": str(data['soilMoisture2']),
            "/SoilMoisture3": str(data['soilMoisture3'])
        }
        
        # Push to Firebase
        ref = db.reference(parent_path)
        ref.update(firebase_data)
        
        print(f"✓ Pushed data to {parent_path}")
        print(f"  Data: {firebase_data}")
        return True
        
    except Exception as e:
        print(f"✗ Firebase error: {e}")
        return False

# Main loop with reconnection logic
print("Starting Arduino to Firebase data logger...")
print("Make sure your firebase-adminsdk.json file is in the same directory!")
print("Don't forget to update the USER_UID in the code!")

# Get user UID (you need to replace this with actual UID)
USER_UID = get_user_uid()
if USER_UID == "your_user_uid_here":
    print("⚠️  WARNING: Please update the USER_UID in the code with your actual Firebase UID!")
    print("   You can find this in your Firebase console or ESP32 serial output")

while True:
    try:
        ser = setup_serial()
        print("Starting data collection...")
        print(f"Connected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Using database path: /lima/{USER_UID}/readings")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"Raw data received: {line}")
                    try:
                        sensor_data = json.loads(line)
                        
                        # Validate data
                        is_valid, message = validate_sensor_data(sensor_data)
                        if is_valid:
                            success = push_to_firebase(sensor_data, USER_UID)
                            if success:
                                print(f"✓ Data successfully sent to Firebase in ESP32 format!")
                        else:
                            print(f"✗ Invalid data: {message} - {sensor_data}")
                            
                    except json.JSONDecodeError:
                        print(f"✗ Invalid JSON received: {line}")
            
            time.sleep(1)
            
    except serial.SerialException as e:
        print(f"Serial connection lost: {e}")
        print("Attempting to reconnect in 5 seconds...")
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)

print("Data logger stopped.")