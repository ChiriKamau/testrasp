import cv2
import firebase_admin
from firebase_admin import credentials, storage, auth
import datetime
import time
import os
import requests
import glob
import json

# Determine absolute path to firebase-adminsdk.json
ABSOLUTE_PATH = '/home/lima/testrasp/firebase-adminsdk.json'  # Replace with your actual absolute path

# Initialize Firebase Admin SDK
cred = credentials.Certificate(ABSOLUTE_PATH)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'espcam-69f58.appspot.com'
})

def check_internet_connection(timeout=5):
    """Check if there's an active internet connection"""
    try:
        # Try to reach Google's DNS server
        response = requests.get('http://www.google.com', timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_uid_from_email(email):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except firebase_admin.auth.AuthError as e:
        print(f"Error getting user: {e}")
        return None

def is_daytime():
    now = datetime.datetime.now()
    # Check if current time is between 6:00 AM and 6:40 PM (18:40)
    start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=18, minute=40, second=0, microsecond=0)
    
    return start_time <= now <= end_time

def ensure_images_folder():
    """Create images folder if it doesn't exist"""
    images_folder = "images"
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        print(f"Created '{images_folder}' folder.")
    return images_folder

def save_upload_queue(queue_file, pending_uploads):
    """Save the list of pending uploads to a JSON file"""
    try:
        with open(queue_file, 'w') as f:
            json.dump(pending_uploads, f, indent=2)
    except Exception as e:
        print(f"Error saving upload queue: {e}")

def load_upload_queue(queue_file):
    """Load the list of pending uploads from a JSON file"""
    try:
        if os.path.exists(queue_file):
            with open(queue_file, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading upload queue: {e}")
        return []

def upload_image_to_firebase(local_filepath, uid, filename):
    """Upload a single image to Firebase Storage"""
    try:
        with open(local_filepath, 'rb') as image_file:
            image_data = image_file.read()
        
        bucket = storage.bucket()
        blob = bucket.blob(f"images2025/{uid}/{filename}")
        blob.upload_from_string(image_data, content_type='image/jpeg')
        print(f"Image '{filename}' uploaded to Firebase Storage.")
        return True
    except Exception as e:
        print(f"Error uploading image '{filename}' to Firebase Storage: {str(e)}")
        return False

def process_upload_queue(uid, queue_file):
    """Process all pending uploads when internet is available"""
    pending_uploads = load_upload_queue(queue_file)
    
    if not pending_uploads:
        return
    
    print(f"Processing {len(pending_uploads)} pending uploads...")
    successful_uploads = []
    
    for upload_info in pending_uploads:
        local_filepath = upload_info['local_filepath']
        filename = upload_info['filename']
        
        # Check if file still exists
        if os.path.exists(local_filepath):
            if upload_image_to_firebase(local_filepath, uid, filename):
                successful_uploads.append(upload_info)
            else:
                # If upload fails, stop processing to avoid overwhelming the connection
                break
        else:
            print(f"Local file '{local_filepath}' no longer exists. Removing from queue.")
            successful_uploads.append(upload_info)  # Remove from queue even if file doesn't exist
    
    # Remove successfully uploaded items from the queue
    if successful_uploads:
        pending_uploads = [item for item in pending_uploads if item not in successful_uploads]
        save_upload_queue(queue_file, pending_uploads)
        print(f"Successfully processed {len(successful_uploads)} uploads.")

def take_and_save_image(uid, queue_file):
    """Take and save image locally, add to upload queue if internet available"""
    if not is_daytime():
        print("It's not daytime. Skipping image capture.")
        return

    # Ensure images folder exists
    images_folder = ensure_images_folder()

    # Initialize the camera
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("Error: Unable to open camera.")
        return
    
    ret, frame = camera.read()
    
    if not ret:
        print("Error: Unable to capture frame.")
        camera.release()
        return
    
    # Generate a filename based on the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.jpg"
    local_filepath = os.path.join(images_folder, filename)
    
    # Save the captured image locally with increased quality
    quality = 99  # You can adjust this value as needed
    success = cv2.imwrite(local_filepath, frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    
    # Release the camera
    camera.release()
    
    if success:
        print(f"Image '{filename}' saved locally to '{local_filepath}'.")
        
        # Check internet connection
        if check_internet_connection():
            print("Internet connection available.")
            
            # Try to upload current image
            if upload_image_to_firebase(local_filepath, uid, filename):
                print("Current image uploaded successfully.")
            else:
                # Add to queue if upload fails
                pending_uploads = load_upload_queue(queue_file)
                pending_uploads.append({
                    'local_filepath': local_filepath,
                    'filename': filename,
                    'timestamp': timestamp
                })
                save_upload_queue(queue_file, pending_uploads)
                print("Current image added to upload queue.")
            
            # Process any pending uploads
            process_upload_queue(uid, queue_file)
        else:
            print("No internet connection. Image saved locally only.")
            # Add to upload queue for later
            pending_uploads = load_upload_queue(queue_file)
            pending_uploads.append({
                'local_filepath': local_filepath,
                'filename': filename,
                'timestamp': timestamp
            })
            save_upload_queue(queue_file, pending_uploads)
            print("Image added to upload queue for when internet is available.")
    else:
        print(f"Error: Failed to save image '{filename}' locally.")

def cleanup_old_images(images_folder, days_to_keep=7):
    """Remove local images older than specified days to prevent storage overflow"""
    try:
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        image_files = glob.glob(os.path.join(images_folder, "*.jpg"))
        
        deleted_count = 0
        for image_file in image_files:
            if os.path.getmtime(image_file) < cutoff_time:
                os.remove(image_file)
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old images (older than {days_to_keep} days).")
    except Exception as e:
        print(f"Error during cleanup: {e}")

# Main execution
if __name__ == "__main__":
    email = "green.74house@gmail.com"
    password = "@greenh74"  # Note: This password is not used in the authentication process
    queue_file = "upload_queue.json"
    
    uid = get_uid_from_email(email)
    if uid:
        print(f"User found. UID: {uid}")
        
        # Ensure images folder exists
        images_folder = ensure_images_folder()
        
        # Loop to capture an image every 15 minutes (900 seconds)
        iteration_count = 0
        while True:
            take_and_save_image(uid, queue_file)
            
            # Perform cleanup every 24 hours (96 iterations of 15 minutes)
            iteration_count += 1
            if iteration_count % 96 == 0:
                cleanup_old_images(images_folder, days_to_keep=7)
            
            time.sleep(900)
    else:
        print("User not found. Exiting.")