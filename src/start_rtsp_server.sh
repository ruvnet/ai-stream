#!/bin/bash

# Function to check if a package is installed
check_package() {
    dpkg -l | grep -qw "$1" || {
        echo "Installing $1..."
        sudo apt-get install -y "$1"
    }
}

# Function to check if a Python package is installed
check_python_package() {
    pip show "$1" > /dev/null 2>&1 || {
        echo "Installing Python package $1..."
        pip install "$1"
    }
}

# Update package list
echo "Updating package list..."
sudo apt-get update

# Check and install GStreamer and plugins
echo "Checking and installing necessary GStreamer packages..."
check_package libgstreamer1.0-dev
check_package gstreamer1.0-plugins-base
check_package gstreamer1.0-plugins-good
check_package gstreamer1.0-plugins-bad
check_package gstreamer1.0-plugins-ugly
check_package gstreamer1.0-libav
check_package gstreamer1.0-tools
check_package gstreamer1.0-rtsp
check_package libgstrtspserver-1.0-dev

# Set environment variables for GStreamer
export GI_TYPELIB_PATH=/usr/lib/girepository-1.0
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu

# Ensure the OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY is not set. Please set the environment variable and try again."
    exit 1
fi

# Export the OpenAI API key for debugging
echo "Debug: OpenAI API Key: $OPENAI_API_KEY"

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Check and install necessary Python packages
check_python_package pygobject
check_python_package opencv-python
check_python_package requests

# Start the RTSP server
echo "Starting the RTSP server..."
python3 rtsp_server.py
