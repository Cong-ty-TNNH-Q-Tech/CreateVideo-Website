#!/bin/bash
# VideoTeaching Docker Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check for NVIDIA Docker runtime
check_gpu() {
    if ! command -v nvidia-smi &> /dev/null; then
        print_warning "NVIDIA GPU not detected. Running in CPU mode."
        export CUDA_VISIBLE_DEVICES=""
        return 1
    fi
    
    if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        print_warning "NVIDIA Docker runtime not available. Install nvidia-container-toolkit."
        return 1
    fi
    
    print_success "GPU support enabled"
    return 0
}

# Check for required files
check_requirements() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env and add your GEMINI_API_KEY"
    fi
    
    if [ ! -d "app/SadTalker/checkpoints" ]; then
        print_warning "SadTalker checkpoints not found."
        print_warning "Please download models using: python download_models.py"
    fi
}

# Build Docker image
build() {
    print_success "Building Docker image..."
    docker-compose build --no-cache
    print_success "Build complete"
}

# Start services
start() {
    check_requirements
    check_gpu
    
    print_success "Starting VideoTeaching..."
    docker-compose up -d
    
    print_success "Application started at http://localhost:5000"
    docker-compose logs -f
}

# Start in development mode
dev() {
    check_requirements
    check_gpu
    
    print_success "Starting VideoTeaching in development mode..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
}

# Stop services
stop() {
    print_success "Stopping VideoTeaching..."
    docker-compose down
}

# View logs
logs() {
    docker-compose logs -f "$@"
}

# Clean up
clean() {
    print_warning "This will remove all containers, volumes, and images. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker-compose down -v --rmi all
        print_success "Cleanup complete"
    fi
}

# Show usage
usage() {
    cat << EOF
VideoTeaching Docker Management

Usage: $0 [command]

Commands:
    build       Build Docker image
    start       Start services in production mode
    dev         Start services in development mode
    stop        Stop all services
    logs        View logs (optional: service name)
    clean       Remove all containers, volumes, and images
    help        Show this help message

Examples:
    $0 build
    $0 start
    $0 dev
    $0 logs videoteaching
    $0 stop

EOF
}

# Main
case "$1" in
    build)
        build
        ;;
    start)
        start
        ;;
    dev)
        dev
        ;;
    stop)
        stop
        ;;
    logs)
        shift
        logs "$@"
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
