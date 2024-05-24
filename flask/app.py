import base64
import os
import cv2
import re
import numpy as np
import requests
import time
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

API_URL = "https://api.openai.com/v1/chat/completions"
API_KEY = os.getenv("OPENAI_API_KEY")

def preprocess_image(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def encode_image_to_base64(image: np.ndarray) -> str:
    success, buffer = cv2.imencode('.jpg', image)
    if not success:
        raise ValueError("Could not encode image to JPEG format.")
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

def compose_payload(image_base64: str, prompt: str) -> dict:
    return {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"You are an expert in analyzing visual content. Please analyze the provided image for the following details:\n"
                            f"1. Identify any text present in the image and provide a summary.\n"
                            f"2. Describe the main objects and their arrangement.\n"
                            f"3. Identify the context of the video frame (e.g., work environment, outdoor scene).\n"
                            f"4. Provide any notable observations about lighting, colors, and overall composition.\n"
                            f"4. Format using markdown.\n"
                            f"Here is the Video Frame still:\n{prompt}"
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2300
    }

def compose_headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

def prompt_image(image_base64: str, prompt: str, api_key: str) -> str:
    headers = compose_headers(api_key=api_key)
    payload = compose_payload(image_base64=image_base64, prompt=prompt)

    while True:
        response = requests.post(url=API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            if 'error' in response_json:
                raise ValueError(response_json['error']['message'])
            return response_json['choices'][0]['message']['content']
        elif response.status_code == 429:
            response_json = response.json()
            error_message = response_json.get('error', {}).get('message', '')
            wait_time = parse_wait_time(error_message)
            if wait_time:
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                time.sleep(wait_time)
            else:
                raise ValueError(f"Rate limit exceeded but could not parse wait time from message: {error_message}")
        else:
            raise ValueError(f"API request failed with status code {response.status_code}: {response.text}")

def parse_wait_time(error_message: str) -> int:
    match = re.search(r"try again in (\d+m)?(\d+\.\ds)?", error_message)
    if match:
        minutes = match.group(1)
        seconds = match.group(2)

        total_wait_time = 0
        if minutes:
            total_wait_time += int(minutes[:-1]) * 60  # Convert minutes to seconds
        if seconds:
            total_wait_time += float(seconds[:-1])  # Add seconds

        return int(total_wait_time)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    image_data = data['image'].split(',')[1]
    image = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    processed_image = preprocess_image(image)
    image_base64 = encode_image_to_base64(processed_image)
    prompt = data.get('prompt', "Analyze this frame")
    api_key = data.get('api_key') or API_KEY
    if not api_key:
        return jsonify({'response': 'API key is required.'}), 400
    try:
        response = prompt_image(image_base64, prompt, api_key)
    except ValueError as e:
        response = str(e)
    return jsonify({'response': response})

if __name__ == '__main__':
    if API_KEY is None:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")
    app.run(debug=True)
