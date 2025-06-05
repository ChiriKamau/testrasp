import serial
import time

print("Testing Arduino connection...")

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    time.sleep(3)  # Give Arduino time to reset after connection
    print("Connected! Listening for data...")
    print("(Remember: your Arduino sends data every 15 minutes)")
    print("Press Ctrl+C to stop")
    
    count = 0
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"[{time.strftime('%H:%M:%S')}] Received: '{line}'")
        
        # Show we're still listening
        count += 1
        if count % 30 == 0:  # Every 30 seconds
            print(f"[{time.strftime('%H:%M:%S')}] Still listening... ({count}s elapsed)")
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nTest stopped by user")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'ser' in locals():
        ser.close()