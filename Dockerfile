# VideoTeaching - Multi-stage Docker build for AI video generation
# Optimized for CUDA 11.8 with SadTalker and VieNeu-TTS

# ============================================================
# Stage 1: Base image with CUDA and Python
# ============================================================
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS base

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ============================================================
# Stage 2: Dependencies installation
# ============================================================
FROM base AS dependencies

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch with CUDA 11.8 support
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchvision==0.15.2 \
    torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

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
