#!/bin/bash

# Function to check if a package is installed
is_installed() {
    dpkg -s "$1" &> /dev/null
}

# Function to check if a Python package is installed
is_python_package_installed() {
    pip3 show "$1" &> /dev/null
}

# Update package list
echo "🔄 Updating package list..."
sudo apt-get update
echo

# Install Python and pip
if ! is_installed python3; then
    echo "🐍 Installing Python..."
    sudo apt-get install -y python3
else
    echo "✔️ Python is already installed."
fi
echo

if ! is_installed python3-pip; then
    echo "📦 Installing pip..."
    sudo apt-get install -y python3-pip
else
    echo "✔️ pip is already installed."
fi
echo

# Install GStreamer dependencies
GSTREAMER_PACKAGES=(
    libgstreamer1.0-0
    gstreamer1.0-plugins-base
    gstreamer1.0-plugins-good
    gstreamer1.0-plugins-ugly
    gstreamer1.0-plugins-bad
    gstreamer1.0-libav
    gstreamer1.0-doc
    gstreamer1.0-tools
    gstreamer1.0-x
    gstreamer1.0-alsa
    gstreamer1.0-pulseaudio
    gstreamer1.0-rtsp
    libgstrtspserver-1.0-dev
)

echo "📡 Installing GStreamer dependencies..."
for pkg in "${GSTREAMER_PACKAGES[@]}"; do
    if ! is_installed "$pkg"; then
        echo "📦 Installing $pkg..."
        sudo apt-get install -y "$pkg"
    else
        echo "✔️ $pkg is already installed."
    fi
done
echo

# Install OpenCV dependencies
if ! is_installed libopencv-dev; then
    echo "📷 Installing OpenCV dependencies..."
    sudo apt-get install -y libopencv-dev python3-opencv
else
    echo "✔️ OpenCV dependencies are already installed."
fi
echo

# Install development tools and cairo dependencies
DEV_TOOLS=(
    build-essential
    cmake
    pkg-config
    libcairo2-dev
    gobject-introspection
    libgirepository1.0-dev
)

echo "🛠️ Installing development tools and cairo dependencies..."
for pkg in "${DEV_TOOLS[@]}"; do
    if ! is_installed "$pkg"; then
        echo "📦 Installing $pkg..."
        sudo apt-get install -y "$pkg"
    else
        echo "✔️ $pkg is already installed."
    fi
done
echo

# Install Python libraries
echo "🐍 Installing Python libraries..."
pip3 install --upgrade pip
echo

PYTHON_PACKAGES=(
    requests
    opencv-python-headless
    pyngrok
    python-dotenv
    pygobject
)

for pkg in "${PYTHON_PACKAGES[@]}"; do
    if ! is_python_package_installed "$pkg"; then
        echo "📦 Installing Python package $pkg..."
        pip3 install "$pkg"
    else
        echo "✔️ Python package $pkg is already installed."
    fi
done
echo

# Install ngrok
if ! command -v ngrok &> /dev/null; then
    echo "🚀 Installing ngrok..."
    wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
    tar -xvf ngrok-v3-stable-linux-amd64.tgz
    sudo mv ngrok /usr/local/bin/ngrok
    rm ngrok-v3-stable-linux-amd64.tgz
else
    echo "✔️ ngrok is already installed."
fi
echo

echo "🎉 All dependencies installed successfully."
