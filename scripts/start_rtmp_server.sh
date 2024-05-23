#!/bin/bash

# Exit on any error
set -e

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Check if NGROK_AUTH_TOKEN is set
if [ -z "$NGROK_AUTH_TOKEN" ]; then
    echo "Error: NGROK_AUTH_TOKEN is not set. Please set it in the .env file."
    exit 1
fi

# Check if Nginx is installed
if ! command -v /usr/local/nginx/sbin/nginx &> /dev/null; then
    echo "Error: Nginx is not installed. Please install Nginx with the RTMP module first."
    exit 1
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "Error: ngrok is not installed. Please install ngrok first."
    exit 1
fi

# Check and stop any processes using ports 1935 and 8080
echo "Checking for processes using ports 1935 and 8080..."
sudo fuser -k 1935/tcp || true
sudo fuser -k 8080/tcp || true

# Start Nginx
echo "Starting Nginx..."
sudo /usr/local/nginx/sbin/nginx

# Authenticate ngrok
echo "Authenticating ngrok..."
ngrok authtoken $NGROK_AUTH_TOKEN

# Start ngrok tunnel for RTMP
echo "Starting ngrok tunnel for RTMP..."
ngrok tcp 1935 &

# Wait for ngrok to establish the tunnel
sleep 5

# Fetch the public URL from ngrok
NGROK_TUNNELS=$(curl -s http://127.0.0.1:4040/api/tunnels)
PUBLIC_URL=$(echo $NGROK_TUNNELS | grep -o '"public_url":"tcp://[^"]*' | sed 's/"public_url":"tcp:\/\///')

if [ -z "$PUBLIC_URL" ]; then
    echo "Error: Could not get public URL from ngrok."
    exit 1
fi

echo "RTMP server is running at rtmp://$PUBLIC_URL/live"

# Instructions for OBS
echo "Configure OBS to stream to: rtmp://$PUBLIC_URL/live"
echo "Stream key: any value (e.g., test)"