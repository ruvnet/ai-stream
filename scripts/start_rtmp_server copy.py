import os
import subprocess
import time
import requests

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Check if NGROK_AUTH_TOKEN is set
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
if not NGROK_AUTH_TOKEN:
    print("Error: NGROK_AUTH_TOKEN is not set. Please set it in the .env file.")
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