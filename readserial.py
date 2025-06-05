import serial
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
import os
from datetime import datetime

# Setup Firebase Admin
cred = credentials.Certificate('/home/lima/testrasp/firebase-adminsdk.json')
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
    return "UByUtYojiSNftinAdQ99CJXnheA2"  # Replace with actual UID

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

def get_current_date():
    """Get current date in YYYY-MM-DD format for folder naming"""
    return datetime.now().strftime("%Y-%m-%d")

def ensure_date_folder():
    """Create data folder structure: data/YYYY-MM-DD/"""
    base_folder = "data"
    current_date = get_current_date()
    date_folder = os.path.join(base_folder, current_date)
    
    # Add debugging
    print(f"Checking/creating folder structure: {date_folder}")
    
    try:
        if not os.path.exists(date_folder):
            os.makedirs(date_folder, exist_ok=True)
            print(f"✓ Created folder: '{date_folder}'")
        else:
            print(f"✓ Folder already exists: '{date_folder}'")
    except Exception as e:
        print(f"✗ Error creating folder '{date_folder}': {e}")
        # Fallback: try to create just the base folder
        try:
            if not os.path.exists(base_folder):
                os.makedirs(base_folder, exist_ok=True)
                print(f"✓ Created base folder: '{base_folder}'")
        except Exception as e2:
            print(f"✗ Error creating base folder '{base_folder}': {e2}")
    
    return date_folder

def save_data_locally(data, uid, timestamp):
    """Save sensor data locally in date-organized folders with daily JSON files"""
    try:
        # Ensure date folder exists
        date_folder = ensure_date_folder()
        current_date = get_current_date()
        
        # JSON filename for the day
        json_filename = f"{current_date}_readings.json"
        json_filepath = os.path.join(date_folder, json_filename)
        
        # Create new reading entry
        new_reading = {
            timestamp: {
                "temperature": str(data['temperature']),
                "humidity": str(data['humidity']),
                "SoilMoisture1": str(data['soilMoisture1']),
                "SoilMoisture2": str(data['soilMoisture2']),
                "SoilMoisture3": str(data['soilMoisture3'])
            }
        }
        
        # Load existing data or create new structure
        daily_data = {
            "date": current_date,
            "uid": uid,
            "readings": {}
        }
        
        # If file exists, load existing data
        if os.path.exists(json_filepath):
            try:
                with open(json_filepath, 'r') as json_file:
                    daily_data = json.load(json_file)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not read existing file {json_filepath}: {e}")
                print("Creating new daily data structure")
        
        # Add new reading to daily data
        daily_data["readings"].update(new_reading)
        
        # Save updated data back to file
        with open(json_filepath, 'w') as json_file:
            json.dump(daily_data, json_file, indent=2)
        
        print(f"✓ Data appended to '{json_filepath}'")
        print(f"  Total readings for {current_date}: {len(daily_data['readings'])}")
        return True
        
    except Exception as e:
        print(f"✗ Error saving data locally: {e}")
        return False

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
        
        # Save data locally first (always save, regardless of Firebase success)
        save_data_locally(data, uid, current_date_time)
        
        # Push to Firebase
        ref = db.reference(parent_path)
        ref.update(firebase_data)
        
        print(f"✓ Pushed data to Firebase at {parent_path}")
        print(f"  Data: {firebase_data}")
        return True
        
    except Exception as e:
        print(f"✗ Firebase error: {e}")
        print("Data is still saved locally.")
        return False

# Main loop with reconnection logic
print("Starting Arduino to Firebase data logger with date-organized local backup...")
print("Make sure your firebase-adminsdk.json file is in the same directory!")
print("Don't forget to update the USER_UID in the code!")

# Test folder creation immediately
print("\n--- Testing folder creation ---")
test_folder = ensure_date_folder()
print(f"Working directory: {os.getcwd()}")
print(f"Test folder path: {os.path.abspath(test_folder)}")
print("--- End folder test ---\n")

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
        print("Data will be organized by date in 'data/YYYY-MM-DD/' folders")
        
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
                                print(f"✓ Data successfully sent to Firebase and saved locally!")
                            else:
                                print(f"✓ Data saved locally (Firebase upload failed)")
                        else:
                            print(f"✗ Invalid data: {message} - {sensor_data}")
                            
                    except json.JSONDecodeError:
                        print(f"✗ Invalid JSON received: {line}")
            else:
                # Add a debug message every 30 seconds when no data is received
                if hasattr(setup_serial, 'last_debug_time'):
                    if time.time() - setup_serial.last_debug_time > 30:
                        print("Waiting for sensor data from Arduino...")
                        setup_serial.last_debug_time = time.time()
                else:
                    setup_serial.last_debug_time = time.time()
            
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