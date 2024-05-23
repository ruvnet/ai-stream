#!/bin/bash

# Update package list and install GStreamer and its plugins
echo "Updating package list..."
sudo apt-get update

echo "Installing GStreamer and plugins..."
sudo apt-get install -y libgstreamer1.0-0 gstreamer1.0-plugins-base \
gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools \
gstreamer1.0-rtsp

# Set environment variables for GStreamer
export GI_TYPELIB_PATH=/usr/lib/girepository-1.0
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python bindings for GStreamer
echo "Installing Python bindings for GStreamer..."
pip install pygobject

# Create the Python script for the RTSP server
echo "Creating rtsp_server.py..."
cat << 'EOF' > rtsp_server.py
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib

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
    server = RTSPServer()
    loop = GLib.MainLoop()
    loop.run()
EOF

# Provide instructions for running the RTSP server
echo "To run the RTSP server, use the following command:"
echo "source venv/bin/activate && python3 rtsp_server.py"

# Provide additional instructions for OBS configuration
echo "To configure OBS to use the RTSP stream:"
echo "1. Open OBS."
echo "2. Add a Media Source: Go to Sources -> + -> Media Source."
echo "3. Uncheck 'Local File'."
echo "4. Enter the RTSP URL: rtsp://localhost:8554/test."
echo "5. Click OK."

echo "Setup complete."
