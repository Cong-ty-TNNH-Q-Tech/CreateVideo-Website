#!/bin/bash
# Pull and run VideoTeaching from GitHub Container Registry

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}VideoTeaching - Pull & Run Script${NC}"
echo -e "${BLUE}======================================${NC}"

# Configuration
REGISTRY="ghcr.io"
REPO="cong-ty-tnnh-q-tech/createvideo-website"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="videoteaching-app"

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}Error: GEMINI_API_KEY environment variable is not set${NC}"
    echo "Please set it with: export GEMINI_API_KEY=your_api_key"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if NVIDIA Docker is available (for GPU support)
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    GPU_FLAG="--gpus all"
else
    echo -e "${BLUE}ℹ No GPU detected, running in CPU mode${NC}"
    GPU_FLAG=""
fi

echo ""
echo -e "${BLUE}Step 1: Pulling image from GHCR...${NC}"
docker pull ${REGISTRY}/${REPO}:${IMAGE_TAG}

echo ""
echo -e "${BLUE}Step 2: Stopping existing container (if any)...${NC}"
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo ""
echo -e "${BLUE}Step 3: Creating necessary directories...${NC}"
mkdir -p data
mkdir -p static/uploads/presentations
mkdir -p static/results
mkdir -p app/SadTalker/checkpoints
mkdir -p app/SadTalker/gfpgan/weights

echo ""
echo -e "${BLUE}Step 4: Starting new container...${NC}"
docker run -d \
  --name ${CONTAINER_NAME} \
  ${GPU_FLAG} \
  -p 5000:5000 \
  -e GEMINI_API_KEY=${GEMINI_API_KEY} \
  -e FLASK_APP=run.py \
  -e FLASK_ENV=production \
  -e PYTHONUNBUFFERED=1 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/uploads:/app/static/uploads \
  -v $(pwd)/static/results:/app/static/results \
  -v $(pwd)/app/SadTalker/checkpoints:/app/app/SadTalker/checkpoints \
  -v $(pwd)/app/SadTalker/gfpgan/weights:/app/app/SadTalker/gfpgan/weights \
  --restart unless-stopped \
  ${REGISTRY}/${REPO}:${IMAGE_TAG}

echo ""
echo -e "${GREEN}✓ Container started successfully!${NC}"
echo ""
echo "Container name: ${CONTAINER_NAME}"
echo "Image: ${REGISTRY}/${REPO}:${IMAGE_TAG}"
echo ""
echo -e "${BLUE}Waiting for application to be ready...${NC}"
sleep 10

# Check if container is running
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo -e "${GREEN}✓ Container is running${NC}"
    echo ""
    echo "View logs: docker logs -f ${CONTAINER_NAME}"
    echo "Stop: docker stop ${CONTAINER_NAME}"
    echo "Access app: http://localhost:5000"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    echo "View logs: docker logs ${CONTAINER_NAME}"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
