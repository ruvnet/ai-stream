#!/bin/bash

# Exit on any error
set -e

# Update and install necessary packages
sudo apt update
sudo apt install -y build-essential libpcre3 libpcre3-dev libssl-dev wget unzip

# Download and compile Nginx with RTMP module
NGINX_VERSION=1.21.6
wget http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz
tar -zxvf nginx-$NGINX_VERSION.tar.gz

# Remove existing nginx-rtmp-module directory if it exists
if [ -d "nginx-rtmp-module" ]; then
    rm -rf nginx-rtmp-module
fi

git clone https://github.com/arut/nginx-rtmp-module.git

cd nginx-$NGINX_VERSION
./configure --with-http_ssl_module --add-module=../nginx-rtmp-module
make
sudo make install

# Configure Nginx for RTMP
sudo tee /usr/local/nginx/conf/nginx.conf > /dev/null <<EOL
worker_processes auto;
events {
    worker_connections 1024;
}
rtmp {
    server {
        listen 1935;
        chunk_size 4096;

        application live {
            live on;
            record off;
        }
    }
}
http {
    server {
        listen 8080;

        location / {
            root html;
        }

        location /stat {
            rtmp_stat all;
            rtmp_stat_stylesheet stat.xsl;
        }

        location /stat.xsl {
            root html;
        }
    }
}
EOL

# Start Nginx
sudo /usr/local/nginx/sbin/nginx

# Install ngrok
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/ngrok

# Authenticate ngrok
NGROK_AUTH_TOKEN="your_ngrok_auth_token"  # Replace with your ngrok auth token
ngrok authtoken $NGROK_AUTH_TOKEN

# Start ngrok tunnel for RTMP
ngrok tcp 1935 &

# Wait for ngrok to establish the tunnel
sleep 5

# Fetch the public URL from ngrok
NGROK_TUNNELS=$(curl -s http://127.0.0.1:4040/api/tunnels)
PUBLIC_URL=$(echo $NGROK_TUNNELS | grep -o '"public_url":"tcp://[^"]*' | sed 's/"public_url":"tcp:\/\///')

echo "RTMP server is running at rtmp://$PUBLIC_URL/live"

# Instructions for OBS
echo "Configure OBS to stream to: rtmp://$PUBLIC_URL/live"
echo "Stream key: any value (e.g., test)"