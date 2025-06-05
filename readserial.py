import serial
import json
import time
import os
from datetime import datetime

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
    """Get a local user identifier (no Firebase needed)"""
    return "local_user_raspberry_pi"

def get_formatted_timestamp():
    """Generate timestamp in the same format as your ESP32 code using Raspberry Pi local time"""
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
        # Check if 'data' exists as a file (not a directory)
        if os.path.exists(base_folder) and not os.path.isdir(base_folder):
            print(f"Warning: '{base_folder}' exists as a file, not a directory!")
            print(f"Renaming existing file to '{base_folder}.backup'")
            os.rename(base_folder, f"{base_folder}.backup")
        
        # Now create the directory structure
        if not os.path.exists(date_folder):
            os.makedirs(date_folder, exist_ok=True)
            print(f"✓ Created folder: '{date_folder}'")
        else:
            print(f"✓ Folder already exists: '{date_folder}'")
            
    except Exception as e:
        print(f"✗ Error creating folder '{date_folder}': {e}")
        
        # Fallback: try using a different base folder name
        try:
            base_folder = "sensor_data"
            date_folder = os.path.join(base_folder, current_date)
            print(f"Trying alternative folder: {date_folder}")
            
            if not os.path.exists(date_folder):
                os.makedirs(date_folder, exist_ok=True)
                print(f"✓ Created alternative folder: '{date_folder}'")
        except Exception as e2:
            print(f"✗ Error creating alternative folder '{date_folder}': {e2}")
    
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
        
        print(f"✓ Data saved to '{json_filepath}'")
        print(f"  Total readings for {current_date}: {len(daily_data['readings'])}")
        return True
        
    except Exception as e:
        print(f"✗ Error saving data locally: {e}")
        return False

def validate_sensor_data(data):
    """Validate sensor data before saving"""
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

def process_sensor_data(data, uid):
    """Process and save sensor data locally (offline mode)"""
    try:
        # Get formatted timestamp
        current_date_time = get_formatted_timestamp()
        
        # Save data locally
        success = save_data_locally(data, uid, current_date_time)
        
        if success:
            print(f"✓ Data successfully saved locally at {current_date_time}")
            print(f"  Temperature: {data['temperature']}°C")
            print(f"  Humidity: {data['humidity']}%")
            print(f"  Soil Moisture 1: {data['soilMoisture1']}")
            print(f"  Soil Moisture 2: {data['soilMoisture2']}")
            print(f"  Soil Moisture 3: {data['soilMoisture3']}")
        
        return success
        
    except Exception as e:
        print(f"✗ Error processing sensor data: {e}")
        return False



# Main execution starts here
print("Starting Arduino to Local Storage data logger (OFFLINE MODE)")
print("No internet connection required!")

# Get user UID (local identifier)
USER_UID = get_user_uid()
print(f"Using local user ID: {USER_UID}")

# Main loop with reconnection logic
while True:
    try:
        ser = setup_serial()
        print("Starting data collection...")
        print(f"Connected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Data will be organized by date in 'data/YYYY-MM-DD/' folders")
        print("All data is stored locally - no internet required!")
        
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
                            success = process_sensor_data(sensor_data, USER_UID)
                            if success:
                                print(f"✓ Data successfully saved locally!")
                            else:
                                print(f"✗ Failed to save data locally")
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