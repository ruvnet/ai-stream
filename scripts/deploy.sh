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