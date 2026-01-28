# VideoTeaching - Docker Deployment Guide

This guide explains how to run VideoTeaching using Docker with GPU support for AI model inference.

## 📋 Prerequisites

### Required
- **Docker** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ (included with Docker Desktop)
- **NVIDIA GPU** with CUDA 11.8+ support (for GPU acceleration)
- **NVIDIA Container Toolkit** ([Installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

### Check GPU Support
```bash
# Test NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

If this works, you have GPU support enabled! 🎉

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

**Important**: Add your `GEMINI_API_KEY` in the `.env` file.

### 2. Download AI Models
Before running Docker, download the required model checkpoints:

```bash
# Download SadTalker checkpoints
python download_models.py
```

This will download models to `app/SadTalker/checkpoints/`.

### 3. Build and Run

#### Using Helper Scripts (Recommended)

**Windows (PowerShell)**:
```powershell
# Build image
.\docker-run.ps1 build

# Start in production mode
.\docker-run.ps1 start

# Or start in development mode
.\docker-run.ps1 dev
```

**Linux/Mac (Bash)**:
```bash
# Make script executable
chmod +x docker-run.sh

# Build image
./docker-run.sh build

# Start in production mode
./docker-run.sh start

# Or start in development mode
./docker-run.sh dev
```

#### Using Docker Compose Directly

**Production**:
```bash
docker-compose up -d
```

**Development** (with live reload):
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4. Access Application
Open your browser: **http://localhost:5000**

## 📁 Project Structure

```
VideoTeaching/
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yml         # Production configuration
├── docker-compose.dev.yml     # Development overrides
├── .dockerignore             # Files to exclude from build
├── .env.example              # Environment template
├── docker-run.sh             # Helper script (Linux/Mac)
├── docker-run.ps1            # Helper script (Windows)
├── README.Docker.md          # This file
└── app/
    └── SadTalker/
        └── checkpoints/      # Mount point for models
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Flask
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secret-key

# AI Services
GEMINI_API_KEY=your_gemini_api_key

# GPU Settings
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=all
```

### Volume Mounts

The Docker Compose configuration mounts several volumes:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./app` | `/app/app` | Application code (read-only in prod) |
| `./templates` | `/app/templates` | HTML templates |
| `./static` | `/app/static` | Static files (uploads, results) |
| `./app/SadTalker/checkpoints` | `/app/app/SadTalker/checkpoints` | AI model checkpoints |
| Named volume `huggingface-cache` | `/root/.cache/huggingface` | VieNeu-TTS models cache |

## 🛠️ Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f videoteaching
```

### Stop Services
```bash
docker-compose down
```

### Rebuild Image
```bash
# Full rebuild
docker-compose build --no-cache

# Rebuild and restart
docker-compose up -d --build
```

### Clean Up
```bash
# Remove containers and volumes
docker-compose down -v

# Remove images too
docker-compose down -v --rmi all
```

### Execute Commands in Container
```bash
# Open shell
docker-compose exec videoteaching bash

# Run Python script
docker-compose exec videoteaching python download_models.py
```

## 🐛 Troubleshooting

### GPU Not Detected
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, install NVIDIA Container Toolkit
# Ubuntu/Debian:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Out of Memory (OOM)
Increase Docker memory limit in Docker Desktop settings or add to `docker-compose.yml`:

```yaml
services:
  videoteaching:
    deploy:
      resources:
        limits:
          memory: 16G  # Adjust based on your system
```

### Models Not Loading
Ensure checkpoints are downloaded and mounted correctly:

```bash
# Check if models exist
ls -lh app/SadTalker/checkpoints/

# Download if missing
python download_models.py
```

### Port Already in Use
Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

## 🔐 Security Best Practices

1. **Never commit** `.env` file with real API keys
2. **Change** `SECRET_KEY` in production
3. **Use** Docker secrets for sensitive data in production:
   ```yaml
   secrets:
     gemini_key:
       file: ./secrets/gemini_api_key.txt
   ```
4. **Run** as non-root user (add to Dockerfile):
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

## 📊 Performance Optimization

### Multi-stage Build
The Dockerfile uses multi-stage builds to:
- Reduce image size (exclude build dependencies)
- Cache Python packages separately
- Speed up rebuilds

### Layer Caching
Dependencies are installed before copying code:
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # Code changes don't rebuild deps
```

### GPU Memory Management
Set CUDA settings in `.env`:
```bash
# Use specific GPU
CUDA_VISIBLE_DEVICES=0

# Limit GPU memory
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

## 📦 Production Deployment

### Using Docker Swarm
```bash
docker stack deploy -c docker-compose.yml videoteaching
```

### Using Kubernetes
Convert to Kubernetes manifests:
```bash
kompose convert -f docker-compose.yml
```

### Cloud Platforms
- **AWS**: Use ECS with GPU instances (p3, g4dn)
- **GCP**: Use GKE with GPU node pools
- **Azure**: Use AKS with GPU-enabled VMs

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PyTorch Docker Images](https://hub.docker.com/r/pytorch/pytorch)

## 🆘 Support

For issues specific to:
- **Docker setup**: Check [Docker Troubleshooting](https://docs.docker.com/config/daemon/)
- **GPU issues**: Check [NVIDIA Container Toolkit Issues](https://github.com/NVIDIA/nvidia-docker/issues)
- **Application errors**: Check application logs with `docker-compose logs -f`

---

**Happy Dockerizing! 🐳**
