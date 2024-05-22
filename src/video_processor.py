import cv2
import base64
import requests
import numpy as np
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
RTSP_STREAM_URL = os.getenv('RTSP_STREAM_URL')
FRAME_RATE = int(os.getenv('FRAME_RATE', 1))

async def process_frame(frame_data):
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
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
