import cv2
import requests
import base64
import time

# URL of the FastAPI app running locally
url = "http://127.0.0.1:8000/process_frame"

# RTSP stream URL
rtsp_url = "rtsp://localhost:8554/mystream"

# Open the RTSP stream
cap = cv2.VideoCapture(rtsp_url)
if not cap.isOpened():
    raise Exception(f"Error opening RTSP stream from {rtsp_url}")

while True:
    # Capture a frame from the RTSP stream
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame. Exiting...")
        break

    # Encode the frame as JPEG
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        print("Error encoding frame.")
        continue

    # Create a form to send the frame
    files = {
        'file': ('frame.jpg', buffer.tobytes(), 'image/jpeg')
    }

    # Send the frame to the FastAPI app
    response = requests.post(url, files=files)

    # Print the response from the FastAPI app
    try:
        response_json = response.json()
        print(response_json)
    except Exception as e:
        print("Error:", e)
        print("Response content is not in JSON format")
        print("Response text:", response.text)

    # Wait for a while before capturing the next frame
    time.sleep(1)

cap.release()
