import gi
import os
import cv2
import base64
import requests
import time
import logging
from threading import Thread
from queue import Queue, Empty
import subprocess
from gi.repository import Gst, GstRtspServer, GObject, GLib
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Configuration
FPS = 1
CHUNK_DURATION = 10  # seconds
API_KEY = os.getenv("OPENAI_API_KEY")  # Use environment variable for API key
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")  # Use environment variable for ngrok auth token
CHUNKED_RESPONSES = True  # Set to False for streaming text responses
MAX_IMAGES = 5  # Maximum number of images to send in one request

# Validate environment variables
if not API_KEY:
    logging.critical("Missing OPENAI_API_KEY environment variable")
    raise ValueError("Missing OPENAI_API_KEY environment variable")
if not NGROK_AUTH_TOKEN:
    logging.critical("Missing NGROK_AUTH_TOKEN environment variable")
    raise ValueError("Missing NGROK_AUTH_TOKEN environment variable")

# Initialize GStreamer
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')

# Start ngrok tunnel using subprocess
logging.info(f"Using ngrok Auth Token: {NGROK_AUTH_TOKEN}")
subprocess.run(["ngrok", "authtoken", NGROK_AUTH_TOKEN], check=True)
ngrok_process = subprocess.Popen(["ngrok", "tcp", "8554"])

time.sleep(5)  # Give ngrok time to establish the tunnel

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
    public_url = public_url.replace("tcp://", "rtsp://")
    RTSP_STREAM_URL = f"{public_url}/test"
    logging.info(f"RTSP server is running at {RTSP_STREAM_URL}")
except requests.exceptions.RequestException as e:
    logging.critical(f"Failed to fetch ngrok tunnel URL: {e}")
    raise

# Function to encode image to base64
def encode_image(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

# Function to send images to GPT-4 Vision API
def send_images_to_gpt4(images):
    if not images:
        return
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    messages = [
        {"role": "user", "content": {"type": "text", "text": "What’s in these images?"}}
    ]
    for image in images[:MAX_IMAGES]:  # Limit the number of images
        messages.append({"role": "user", "content": {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image}"}})
    
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": messages,
        "max_tokens": 300
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"GPT-4 Vision API response: {response.json()}")
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        logging.error(f"Response: {response.text if response else 'No response'}")

# Function to capture frames from RTSP stream
def capture_frames(queue):
    logging.debug(f"Attempting to capture frames from {RTSP_STREAM_URL}")
    cap = cv2.VideoCapture(RTSP_STREAM_URL)
    if not cap.isOpened():
        logging.error(f"Error: Could not open video stream from {RTSP_STREAM_URL}")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Error: Failed to read frame from stream")
            break
        logging.debug("Captured frame from stream")
        queue.put(frame)
        time.sleep(1 / FPS)
    cap.release()

# Function to process frames and send to GPT-4 Vision API
def process_frames(queue):
    while True:
        images = []
        start_time = time.time()
        while time.time() - start_time < CHUNK_DURATION:
            try:
                frame = queue.get(timeout=1)
                images.append(encode_image(frame))
            except Empty:
                pass
        if images:
            logging.info(f"Sending {len(images)} images to GPT-4 Vision API")
            send_images_to_gpt4(images)

# RTSP Server class
class RTSPServer:
    def __init__(self):
        Gst.init(None)
        self.server = GstRtspServer.RTSPServer()
        self.factory = GstRtspServer.RTSPMediaFactory()
        self.factory.set_launch("( videotestsrc ! x264enc ! rtph264pay name=pay0 pt=96 )")
        self.factory.set_shared(True)
        self.server.get_mount_points().add_factory("/test", self.factory)
        self.server.attach(None)
        logging.info("RTSP server is running at rtsp://localhost:8554/test")

if __name__ == "__main__":
    logging.info("Starting RTSP server...")
    server = RTSPServer()
    
    # Create a queue to hold frames
    frame_queue = Queue()
    
    # Start frame capture thread
    capture_thread = Thread(target=capture_frames, args=(frame_queue,))
    capture_thread.start()
    
    # Start frame processing thread
    process_thread = Thread(target=process_frames, args=(frame_queue,))
    process_thread.start()
    
    # Run the main loop
    loop = GLib.MainLoop()
    logging.info("Entering main loop...")
    loop.run()
    
    # Ensure ngrok process is terminated when the script ends
    ngrok_process.terminate()
    logging.info("ngrok process terminated")
