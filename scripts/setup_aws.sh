#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Download the AWS CLI installer
download_aws_cli() {
    echo "Downloading AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
}

# Unzip the installer
unzip_aws_cli() {
    echo "Unzipping AWS CLI..."
    unzip awscliv2.zip
}

# Install the AWS CLI
install_aws_cli() {
    echo "Installing AWS CLI..."
    sudo ./aws/install
}

# Verify the installation
verify_installation() {
    if command_exists aws; then
        echo "AWS CLI installation successful. Version:"
        aws --version
    else
        echo "AWS CLI installation failed."
        exit 1
    fi
}

# Main function
main() {
    if command_exists aws; then
        echo "AWS CLI is already installed. Version:"
        aws --version
    else
        download_aws_cli
        unzip_aws_cli
        install_aws_cli
        verify_installation
    fi
}

# Run the main function
main

# Clean up
rm -rf awscliv2.zip aws/
