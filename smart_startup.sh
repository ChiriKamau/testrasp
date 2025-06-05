#!/bin/bash
cd /home/lima/testrasp

echo "Starting smart startup script..."

# Function to check if Arduino is connected and responsive
check_arduino_ready() {
    # Check if Arduino is physically connected
    if [ ! -e /dev/ttyACM0 ]; then
        echo "Arduino not detected on /dev/ttyACM0"
        return 1
    fi
    
    # Try to read from Arduino
    timeout 30 python3 -c "
import serial
import time
import json

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    time.sleep(3)
    
    for i in range(30):  # Try for 30 seconds
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line and '{' in line:
                print('Arduino is sending data!')
                exit(0)
        time.sleep(1)
    
    print('No data from Arduino')
    exit(1)
except Exception as e:
    print(f'Arduino check failed: {e}')
    exit(1)
"
    return $?
}

# Wait for Arduino to be ready
echo "Checking if Arduino is ready..."
for attempt in {1..20}; do  # Try for 10 minutes (20 x 30 seconds)
    if check_arduino_ready; then
        echo "✓ Arduino is ready!"
        break
    else
        echo "Arduino not ready, attempt $attempt/20. Waiting 30 seconds..."
        sleep 30
    fi
    
    if [ $attempt -eq 20 ]; then
        echo "❌ Arduino failed to respond after 10 minutes"
        exit 1
    fi
done

# Start readserial
echo "Starting readserial..."
python3 readserial > /home/lima/arduino_log.txt 2>&1 &
READSERIAL_PID=$!

# Wait for readserial to establish connection
sleep 45

# Check if readserial is working
if kill -0 $READSERIAL_PID 2>/dev/null; then
    # Check if it's actually working (look for recent activity in logs)
    if tail -n 10 /home/lima/arduino_log.txt | grep -q -E "(Pushed data|Connected|Received)"; then
        echo "✓ readserial is working, starting imagestofirebase..."
        python3 imagestofirebase.py > /home/lima/images_log.txt 2>&1 &
        echo "✓ Both scripts are now running"
    else
        echo "❌ readserial started but not receiving data"
    fi
else
    echo "❌ readserial process died"
fi

# Keep script running
wait