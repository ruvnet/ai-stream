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