#!/bin/bash

# Backend Production Build Script
set -e

# Configuration
IMAGE_NAME="perplexity-oss-backend"
REGION="us-east-1"  # Change as needed
ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"  # Set this environment variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building production image for backend...${NC}"

# Check if AWS_ACCOUNT_ID is set
if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID environment variable is not set${NC}"
    echo "Please set it with: export AWS_ACCOUNT_ID=your-account-id"
    exit 1
fi

# ECR repository URL
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
FULL_IMAGE_NAME="${ECR_URI}/${IMAGE_NAME}"

# Get git commit hash for tagging
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
IMAGE_TAG="${GIT_HASH}"

echo -e "${YELLOW}Building Docker image: ${FULL_IMAGE_NAME}:${IMAGE_TAG}${NC}"

# Build the Docker image
docker build -f prod.Dockerfile -t "${FULL_IMAGE_NAME}:${IMAGE_TAG}" .
docker tag "${FULL_IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE_NAME}:latest"

echo -e "${GREEN}✅ Backend image built successfully!${NC}"
echo -e "${GREEN}Image: ${FULL_IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "${GREEN}Latest: ${FULL_IMAGE_NAME}:latest${NC}"

# Optional: Push to ECR (uncomment to enable)
# echo -e "${YELLOW}Logging in to ECR...${NC}"
# aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

# echo -e "${YELLOW}Pushing image to ECR...${NC}"
# docker push "${FULL_IMAGE_NAME}:${IMAGE_TAG}"
# docker push "${FULL_IMAGE_NAME}:latest"

# echo -e "${GREEN}✅ Backend image pushed to ECR successfully!${NC}"

echo -e "${YELLOW}To push to ECR, run:${NC}"
echo -e "aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI"
echo -e "docker push ${FULL_IMAGE_NAME}:${IMAGE_TAG}"
echo -e "docker push ${FULL_IMAGE_NAME}:latest"