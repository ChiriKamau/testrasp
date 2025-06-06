import cv2
import firebase_admin
from firebase_admin import credentials, storage, auth
import datetime
import time
import os

# Determine absolute path to firebase-adminsdk.json
ABSOLUTE_PATH = '/home/lima/testrasp/firebase-adminsdk.json'  # Replace with your actual absolute path

# Initialize Firebase Admin SDK
cred = credentials.Certificate(ABSOLUTE_PATH)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'espcam-69f58.appspot.com'
})

def get_uid_from_email(email):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except firebase_admin.auth.AuthError as e:
        print(f"Error getting user: {e}")
        return None

def is_daytime():
    now = datetime.datetime.now()
    # Assuming daytime is between 6 AM and 6 PM
    return 6 <= now.hour < 18

def ensure_images_folder():
    """Create images folder if it doesn't exist"""
    images_folder = "images"
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        print(f"Created '{images_folder}' folder.")
    return images_folder

def take_and_upload_image(uid):
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
    
    if success:
        print(f"Image '{filename}' saved locally to '{local_filepath}'.")
    else:
        print(f"Error: Failed to save image '{filename}' locally.")
        camera.release()
        return
    
    # Release the camera
    camera.release()
    
    # Upload the image to Firebase Storage
    try:
        # Read the saved image file for upload
        with open(local_filepath, 'rb') as image_file:
            image_data = image_file.read()
        
        bucket = storage.bucket()
        blob = bucket.blob(f"images2025/{uid}/{filename}")
        blob.upload_from_string(image_data, content_type='image/jpeg')
        print(f"Image '{filename}' uploaded to Firebase Storage.")
    except Exception as e:
        print(f"Error uploading image '{filename}' to Firebase Storage: {str(e)}")
        print(f"Image is still saved locally at '{local_filepath}'.")

# Main execution
if __name__ == "__main__":
    email = "green.74house@gmail.com"
    password = "@greenh74"  # Note: This password is not used in the authentication process
    
    uid = get_uid_from_email(email)
    if uid:
        print(f"User found. UID: {uid}")
        
        # Loop to capture an image and upload it to Firebase every 15 minutes (900 seconds)
        while True:
            take_and_upload_image(uid)
            time.sleep(900)
    else:
        print("User not found. Exiting.")