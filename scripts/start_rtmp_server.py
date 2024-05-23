import os
import subprocess
import time
import requests
import cv2
import base64
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if NGROK_AUTH_TOKEN is set
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
if not NGROK_AUTH_TOKEN:
    print("Error: NGROK_AUTH_TOKEN is not set. Please set it in the .env file.")
    exit(1)

# Check if OPENAI_API_KEY is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set. Please set it in the .env file.")
    exit(1)

# Check if Nginx is installed
if not os.path.exists("/usr/local/nginx/sbin/nginx"):
    print("Error: Nginx is not installed. Please install Nginx with the RTMP module first.")
    exit(1)

# Check if ngrok is installed
if not subprocess.run(["which", "ngrok"], capture_output=True).stdout:
    print("Error: ngrok is not installed. Please install ngrok first.")
    exit(1)

# Check and stop any processes using ports 1935 and 8080
print("Checking for processes using ports 1935 and 8080...")
subprocess.run(["sudo", "fuser", "-k", "1935/tcp"], stderr=subprocess.DEVNULL)
subprocess.run(["sudo", "fuser", "-k", "8080/tcp"], stderr=subprocess.DEVNULL)

# Start Nginx
print("Starting Nginx...")
subprocess.run(["sudo", "/usr/local/nginx/sbin/nginx"])

# Authenticate ngrok
print("Authenticating ngrok...")
subprocess.run(["ngrok", "authtoken", NGROK_AUTH_TOKEN])

# Start ngrok tunnel for RTMP
print("Starting ngrok tunnel for RTMP...")
ngrok_process = subprocess.Popen(["ngrok", "tcp", "1935"])

# Wait for ngrok to establish the tunnel
time.sleep(5)

# Fetch the public URL from ngrok
try:
    response = requests.get('http://127.0.0.1:4040/api/tunnels')
    response.raise_for_status()
    tunnels = response.json()['tunnels']
    public_url = None
    for tunnel in tunnels:
        if tunnel['proto'] == 'tcp':
            public_url = tunnel['public_url']
            break
    if not public_url:
        raise RuntimeError("Could not get public URL from ngrok")
    public_url = public_url.replace("tcp://", "rtmp://")
    rtmp_stream_url = f"{public_url}/live"
    print(f"RTMP server is running at {rtmp_stream_url}")
except requests.exceptions.RequestException as e:
    print(f"Error: Failed to fetch ngrok tunnel URL: {e}")
    ngrok_process.terminate()
    exit(1)

# Instructions for OBS
print(f"Configure OBS to stream to: {rtmp_stream_url}")
print("Stream key: any value (e.g., test)")

# Function to process frames and send to OpenAI Vision API
def process_frame(frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return "Error encoding frame."

    base64_image = base64.b64encode(buffer).decode('utf-8')

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-4-vision-preview',
        'image': base64_image,
        'detail': 'high'
    }

    response = requests.post('https://api.openai.com/v1/images', headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('text', 'No response')
    else:
        return f"Error: {response.status_code}"

# Wait for the RTMP stream to be available
RTSP_STREAM_URL = os.getenv('RTSP_STREAM_URL')
FRAME_RATE = int(os.getenv('FRAME_RATE', 1))

print("Waiting for the RTMP stream to be available...")
while True:
    cap = cv2.VideoCapture(RTSP_STREAM_URL)
    if cap.isOpened():
        print("RTMP stream is now available.")
        break
    print("RTMP stream not available yet. Retrying in 5 seconds...")
    time.sleep(5)

print("Starting to capture frames from the RTSP stream...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to read frame from stream")
        break

    result = process_frame(frame)
    print(f"Processed frame result: {result}")

    time.sleep(1 / FRAME_RATE)

cap.release()