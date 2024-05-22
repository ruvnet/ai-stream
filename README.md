# AI Stream

This project sets up a video processing service on AWS ECS that accepts an RTSP stream, converts it to base64 images, and sends them to the GPT-4 Vision API for processing. The processed responses, which include descriptions of the video stream, are then returned.

## Project Structure

```
ai-stream/
├── src/
│   ├── app.py
│   ├── video_processor.py
│   ├── Dockerfile
│   ├── requirements.txt
├── scripts/
│   ├── deploy.sh
│   ├── create_ecs_resources.py
│   ├── setup.sh
├── .env
├── .gitignore
├── README.md
```

## Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone https://github.com/ruvnet/ai-stream.git
   cd ai-stream
   ```

2. **Run the setup script**:

   ```bash
   ./scripts/setup.sh
   ```

3. **Set environment variables**:
   - Create a `.env` file in the project root and fill in the required environment variables:

     ```plaintext
     OPENAI_API_KEY=your_openai_api_key
     RTSP_STREAM_URL=your_rtsp_stream_url
     FRAME_RATE=1
     AWS_ACCOUNT_ID=your_aws_account_id
     EXECUTION_ROLE_ARN=your_execution_role_arn
     TASK_ROLE_ARN=your_task_role_arn
     SUBNET_ID=your_subnet_id
     ```

4. **Build and push Docker image to ECR**:

   ```bash
   ./scripts/deploy.sh
   ```

5. **Create ECS resources**:

   ```bash
   python scripts/create_ecs_resources.py
   ```

6. **Start the service**:
   - The service will start automatically in AWS ECS and begin processing the RTSP stream.

## Notes

- Ensure you replace placeholder values in the `.env` file with your actual values.
- The ECS service will continuously process frames from the RTSP stream, send them to the GPT-4 Vision API, and return text descriptions of the video stream.

## Source Files

### `src/app.py`

```python
from quart import Quart, request, jsonify
from video_processor import process_frame
import os

app = Quart(__name__)

@app.route('/process_frame', methods=['POST'])
async def process_frame_endpoint():
    try:
        files = await request.files
        if 'frame' not in files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = files['frame']
        file_content = await file.read()
        response = await process_frame(file_content)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### `src/video_processor.py`

```python
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

def capture_frames():
    cap = cv2.VideoCapture(RTSP_STREAM_URL)
    if not cap.isOpened():
        raise Exception(f"Error opening RTSP stream from {RTSP_STREAM_URL}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        response = process_frame(cv2.imencode('.jpg', frame)[1].tobytes())
        print(response)  # For debugging, replace with appropriate logging

        # Sleep to control frame rate
        cv2.waitKey(int(1000 / FRAME_RATE))

    cap.release()
```

### `src/Dockerfile`

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

### `src/requirements.txt`

```plaintext
quart
opencv-python-headless
requests
```

### `scripts/deploy.sh`

```bash
#!/bin/bash

# Variables
AWS_REGION=us-west-2
ECR_REPOSITORY=my_video_processor_repo
IMAGE_TAG=latest

# Build Docker image
docker build -t $ECR_REPOSITORY:$IMAGE_TAG ./src

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# Push Docker image to ECR
docker tag $ECR_REPOSITORY:$IMAGE_TAG $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
docker push $(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
```

### `scripts/create_ecs_resources.py`

```python
import boto3
import os

AWS_REGION = 'us-west-2'
CLUSTER_NAME = 'my_video_processor_cluster'
TASK_DEFINITION_NAME = 'my_video_processor_task'
SERVICE_NAME = 'my_video_processor_service'
ECR_REPOSITORY = 'my_video_processor_repo'
IMAGE_TAG = 'latest'

def create_ecs_resources():
    client = boto3.client('ecs', region_name=AWS_REGION)

    # Create ECS Cluster
    client.create_cluster(clusterName=CLUSTER_NAME)

    # Register Task Definition
    response = client.register_task_definition(
        family=TASK_DEFINITION_NAME,
        networkMode='awsvpc',
        containerDefinitions=[
            {
                'name': 'my_video_processor_container',
                'image': f'{os.environ["AWS_ACCOUNT_ID"]}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPOSITORY}:{IMAGE_TAG}',
                'memory': 512,
                'cpu': 256,
                'essential': True,
                'portMappings': [
                    {
                        'containerPort': 5000,
                        'hostPort': 5000,
                        'protocol': 'tcp'
                    }
                ],
                'environment': [
                    {'name': 'OPENAI_API_KEY', 'value': os.environ['OPENAI_API_KEY']},
                    {'name': 'RTSP_STREAM_URL', 'value': os.environ['RTSP_STREAM_URL']},
                    {'name': 'FRAME_RATE', 'value': os.environ['FRAME_RATE']}
                ]
            }
        ],
        requiresCompatibilities=['FARGATE'],
        executionRoleArn=os.environ['EXECUTION_ROLE_ARN'],
        taskRoleArn=os.environ['TASK_ROLE_ARN'],
        memory='1024',
        cpu='512'
    )

    # Create ECS Service
    client.create_service(
        cluster=CLUSTER_NAME,
        serviceName=SERVICE_NAME,
        taskDefinition=TASK_DEFINITION_NAME,
        desiredCount=1,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [os.environ['SUBNET_ID']],
                'assignPublicIp': 'ENABLED'
            }
        }
    )

if __name__ == "__main__":
    create_ecs_resources()
```

### `scripts/setup.sh`

```bash
#!/bin/bash

# Create project directories
mkdir -p src scripts

# Create source files
touch src/app.py src/video_processor.py src/Dockerfile src/requirements.txt

# Create script files
touch scripts/deploy.sh scripts/create_ecs_resources.py scripts/setup.sh

# Create .env file
touch .env

# Create README.md
touch README.md
```

### Example Client Script to Test the Endpoint

Here’s an example client script that you can use to test your endpoint. This script will capture a frame from your local webcam, send it to the Quart app running in your ECS container, and print the response.

### `client_test.py`

```python
import cv2
import requests
import base64

# URL of the Quart app running in your ECS container
url = "http://YOUR_ECS_SERVICE_PUBLIC_IP:5000/process_frame"

# Capture a frame from your webcam
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

```python
# Encode the frame as JPEG
ret, buffer = cv2.imencode('.jpg', frame)
if not ret:
    raise Exception("Error encoding frame.")

# Create a form to send the frame
files = {
    'frame': ('frame.jpg', buffer.tobytes(), 'image/jpeg')
}

# Send the frame to the Quart app
response = requests.post(url, files=files)

# Print the response from the Quart app
try:
    response_json = response.json()
    print(response_json)
except requests.exceptions.JSONDecodeError:
    print("Response content is not in JSON format")
    print("Response text:", response.text)
```

## Final Notes

- Ensure all the required AWS IAM roles and permissions are set up correctly.
- Ensure the `.env` file contains all the necessary environment variables.
- Replace placeholders with your actual AWS and OpenAI credentials.
- The ECS service will continuously process frames from the RTSP stream, send them to the GPT-4 Vision API, and return text descriptions of the video stream.

### Testing the RTSP Stream

If you need to test the RTSP stream locally, you can use OBS (Open Broadcaster Software) to stream video from your local machine. Set OBS to stream to an RTSP server or use a local RTSP server setup to provide a stream URL that can be used in the `.env` file.

To make the RTSP stream available publicly for testing on GitHub Codespaces, ensure your local network allows for public access or use a service that provides a publicly accessible RTSP stream.

