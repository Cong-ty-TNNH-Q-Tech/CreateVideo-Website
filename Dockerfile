# VideoTeaching - Multi-stage Docker build for AI video generation
# Optimized for CUDA 11.8 with SadTalker and VieNeu-TTS

# ============================================================
# Stage 1: Base image with CUDA and Python
# ============================================================
# ============================================================
# Stage 1: Base image with CUDA and Python
# ============================================================
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS base

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3.11-distutils \
    git \
    wget \
    curl \
    ffmpeg \
    build-essential \
    cmake \
    libsndfile1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Create symbolic links for python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/local/bin/pip /usr/bin/pip

# ============================================================
# Stage 2: Dependencies installation
# ============================================================
FROM base AS dependencies

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch independently with CUDA 11.8 support
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    torchvision==0.20.1 \
    torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu118

# Install dependencies from requirements.txt
# Remove conflicting system blinker if present
RUN pip install --no-cache-dir --ignore-installed blinker -r requirements.txt

# Fix BasicSR compatibility with newer TorchVision
# Replace 'from torchvision.transforms.functional_tensor import rgb_to_grayscale'
# with 'from torchvision.transforms.functional import rgb_to_grayscale'
RUN sed -i 's/from torchvision.transforms.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/g' \
    /usr/local/lib/python3.11/dist-packages/basicsr/data/degradations.py

# ============================================================
# Stage 3: Application
# ============================================================
FROM dependencies AS application

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    static/uploads/presentations \
    static/results \
    data \
    app/SadTalker/checkpoints \
    app/SadTalker/gfpgan/weights

# Download SadTalker checkpoints (if not mounted)
RUN if [ ! -f app/SadTalker/checkpoints/epoch_20.pth ]; then \
    echo "Checkpoints should be mounted or downloaded separately"; \
    fi

# Set proper permissions
RUN chmod -R 755 /app/static && \
    chmod -R 777 /app/static/results && \
    chmod -R 777 /app/static/uploads

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "run.py"]
