import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib
import os

import cv2
import base64
import requests
import time
from threading import Thread
from queue import Queue, Empty

# Configuration
RTSP_STREAM_URL = "rtsp://localhost:8554/test"
FPS = 1
CHUNK_DURATION = 10  # seconds
API_KEY = os.getenv("OPENAI_API_KEY")  # Use environment variable for API key
CHUNKED_RESPONSES = True  # Set to False for streaming text responses

# Function to encode image to base64
def encode_image(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

# Function to send images to GPT-4 Vision API
def send_images_to_gpt4(images):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    messages = [
        {"role": "user", "content": {"type": "text", "text": "What’s in these images?"}}
    ]
    for image in images:
        messages.append({"role": "user", "content": {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image}"}})
    
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": messages,
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code}, Message: {response.json()}")

# Function to capture frames from RTSP stream
def capture_frames(queue):
    cap = cv2.VideoCapture(RTSP_STREAM_URL)
    if not cap.isOpened():
        print(f"Error: Could not open video stream from {RTSP_STREAM_URL}")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame from stream")
            break
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
        print("RTSP server is running at rtsp://localhost:8554/test")

if __name__ == "__main__":
    # Start RTSP server
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
    loop.run()
