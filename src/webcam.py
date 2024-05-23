import base64
import os
import uuid

import cv2
import gradio as gr
import numpy as np
import requests

MARKDOWN = """
# WebcamGPT 💬 + 📸

webcamGPT is a tool that allows you to chat with video using OpenAI Vision API.

Visit [awesome-openai-vision-api-experiments](https://github.com/roboflow/awesome-openai-vision-api-experiments) 
repository to find more OpenAI Vision API experiments or contribute your own.
"""
AVATARS = (
    "https://media.roboflow.com/spaces/roboflow_raccoon_full.png",
    "https://media.roboflow.com/spaces/openai-white-logomark.png"
)
IMAGE_CACHE_DIRECTORY = "data"
API_URL = "https://api.openai.com/v1/chat/completions"


def preprocess_image(image: np.ndarray) -> np.ndarray:
    if image.ndim < 2:
        raise ValueError("Input image must be >= 2-d.")
    image = np.fliplr(image)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


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
                        "text": prompt
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
        "max_tokens": 300
    }


def compose_headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }


def prompt_image(api_key: str, image_base64: str, prompt: str) -> str:
    headers = compose_headers(api_key=api_key)
    payload = compose_payload(image_base64=image_base64, prompt=prompt)
    print("Payload:", payload)  # Debug: Print the payload
    response = requests.post(url=API_URL, headers=headers, json=payload)
    print("Response:", response.text)  # Debug: Print the response text

    response_json = response.json()
    if 'error' in response_json:
        raise ValueError(response_json['error']['message'])
    return response_json['choices'][0]['message']['content']


def cache_image(image: np.ndarray) -> str:
    image_filename = f"{uuid.uuid4()}.jpeg"
    os.makedirs(IMAGE_CACHE_DIRECTORY, exist_ok=True)
    image_path = os.path.join(IMAGE_CACHE_DIRECTORY, image_filename)
    cv2.imwrite(image_path, image)
    return image_path


def respond(image: np.ndarray, prompt: str, chat_history):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API_KEY is not set. "
            "Please follow the instructions in the README to set it up.")

    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        print("Image is None or invalid")  # Debug: Print image invalid message
        raise ValueError("Invalid image input.")

    try:
        image = preprocess_image(image=image)
        cached_image_path = cache_image(image)
        image_base64 = encode_image_to_base64(image)
        response = prompt_image(api_key=api_key, image_base64=image_base64, prompt=prompt)
        chat_history.append(((cached_image_path,), None))
        chat_history.append((prompt, response))
        return "", chat_history
    except Exception as e:
        print(f"Error: {e}")
        raise


with gr.Blocks() as demo:
    gr.Markdown(MARKDOWN)
    with gr.Row():
        webcam = gr.Webcam()  # Use Webcam component to capture images
        with gr.Column():
            chatbot = gr.Chatbot(
                height=500, bubble_full_width=False, avatar_images=AVATARS)
            message_textbox = gr.Textbox()
            capture_button = gr.Button("Capture Image")
            clear_button = gr.ClearButton([message_textbox, chatbot])

    def capture_image(image, prompt, chat_history):
        if image is None:
            print("No image received from webcam")  # Debug: Print no image received message
        else:
            print(f"Image shape: {image.shape}")  # Debug: Print image shape
        return respond(image, prompt, chat_history)

    capture_button.click(
        fn=capture_image,
        inputs=[webcam, message_textbox, chatbot],
        outputs=[message_textbox, chatbot]
    )

demo.launch(debug=False, show_error=True)
