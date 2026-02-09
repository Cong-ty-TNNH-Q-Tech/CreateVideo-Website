# VideoTeaching - AI-Powered Video Presentation Generator

Tự động tạo video thuyết trình với avatar nói chuyện sử dụng AI (SadTalker + VieNeu-TTS)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![CUDA](https://img.shields.io/badge/CUDA-11.8-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![GHCR](https://img.shields.io/badge/GHCR-Images-purple.svg)](https://github.com/Cong-ty-TNNH-Q-Tech/CreateVideo-Website/pkgs/container/createvideo-website)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/Cong-ty-TNNH-Q-Tech/CreateVideo-Website/docker-build-push.yml?label=Docker%20Build)](https://github.com/Cong-ty-TNNH-Q-Tech/CreateVideo-Website/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🎬 **SadTalker Video Generation** - Tạo video talking head từ ảnh tĩnh + audio
- 🎤 **VieNeu-TTS** - Chuyển văn bản tiếng Việt thành giọng nói tự nhiên
- 🎭 **Voice Cloning** - Clone giọng nói từ file audio hoặc ghi âm trực tiếp
- 🤖 **Multi-Model Support** - Chọn model TTS (GGUF Q4/Q8, PyTorch) tùy theo CPU/GPU
- 🧠 **Google Gemini** - Tự động tạo script thuyết trình từ slide PowerPoint/PDF
- 📊 **Presentation Processing** - Đọc và xử lý file PPTX, PPT, PDF
- 🎨 **Modern UI** - Giao diện Bootstrap 5 responsive, dễ sử dụng
- 🐳 **Docker Ready** - Triển khai dễ dàng với Docker Compose + GPU support

## 🚀 Quick Start

### Option 1: Pre-built Docker Image (Fastest ⚡)

Pull optimized image từ GitHub Container Registry - đã được tối ưu hóa với docker-slim!

**Prerequisites:**
- Docker Desktop 20.10+
- NVIDIA GPU + NVIDIA Container Toolkit (for GPU acceleration)

```bash
# Set your API key
export GEMINI_API_KEY=your_api_key_here
# Windows PowerShell: $env:GEMINI_API_KEY = "your_api_key_here"

# Run the pull and run script
bash scripts/pull-and-run.sh
# Windows: .\scripts\pull-and-run.ps1
```

**Access:** http://localhost:5000

📦 **[See deployment guide →](docs/DOCKER_DEPLOYMENT.md)**

### Option 2: Build Docker Locally

**Prerequisites:**
- Docker Desktop 20.10+
- NVIDIA GPU + NVIDIA Container Toolkit (for GPU acceleration)

```bash
# 1. Clone repository
git clone https://github.com/Cong-ty-TNNH-Q-Tech/CreateVideo-Website.git
cd VideoTeaching

# 2. Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Download AI models
python download_models.py

# 4. Run with Docker
.\docker-run.ps1 build    # Build image
.\docker-run.ps1 start    # Start production
# or
.\docker-run.ps1 dev      # Start development mode
```

**Access:** http://localhost:5000

📚 **[See full Docker documentation →](README.Docker.md)**

### Option 3: Local Development

**Prerequisites:**
- Python 3.10+
- CUDA 11.8+ (for GPU acceleration)
- FFmpeg

**Installation:**

```bash
# 1. Clone repository
git clone https://github.com/Cong-ty-TNNH-MoneyEveryWhere/CreateVideo-Website.git
cd VideoTeaching

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install PyTorch with CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 5. Install dependencies
pip install -r requirements.txt

# 6. Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 7. Download AI models
python download_models.py

# 8. Run application
python run.py
```

**Access:** http://localhost:5000

## 📁 Project Structure

```
VideoTeaching/
├── app/
│   ├── controllers/        # API routes and handlers
│   │   ├── main.py        # Main routes, test pages
│   │   └── generation.py  # SadTalker & TTS API endpoints
│   ├── services/          # Business logic
│   │   ├── gemini_service.py    # Google Gemini integration
│   │   └── video_generator.py  # SadTalker wrapper
│   ├── models/            # Data models
│   ├── utils/             # Utilities (presentation reader)
│   ├── SadTalker/         # SadTalker model (submodule)
│   └── VieNeu-TTS/        # VieNeu-TTS model (submodule)
├── templates/             # HTML templates
│   ├── presentation.html  # Main presentation upload page
│   ├── test_sadtalker.html  # SadTalker test page
│   └── test_tts.html      # VieNeu-TTS test page
├── static/                # Static files
│   ├── uploads/           # Uploaded presentations
│   └── results/           # Generated videos/audio
├── tests/                 # Unit & integration tests
├── docs/ai/              # AI DevKit documentation
├── Dockerfile            # Multi-stage Docker build
├── docker-compose.yml    # Production Docker config
├── docker-compose.dev.yml # Development Docker config
├── requirements.txt      # Python dependencies
├── config.py            # Flask configuration
└── run.py               # Application entry point
```

## 🎯 Usage

### 1. Test TTS (Text-to-Speech)
Navigate to: http://localhost:5000/test/tts

- **Text Input:** Nhập văn bản tiếng Việt cần đọc
- **Model Selection:** Chọn model TTS (Q4-GGUF cho CPU, Q8/PyTorch cho GPU)
- **Voice Selection:**
  - Giọng preset: Tuyên, Ngọc, Ly, Bình, Vĩnh, Đoan
  - Voice cloning: Upload audio mẫu hoặc ghi âm trực tiếp
- **Generate:** Tạo giọng nói và tải về file WAV

### 2. Test SadTalker (Video Generation)
Navigate to: http://localhost:5000/test/sadtalker

- **Image:** Upload ảnh chân dung (portrait photo)
- **Audio:** Upload file audio hoặc dùng TTS
- **Generate:** Tạo video talking head
- **Download:** Tải về video MP4

### 3. Presentation to Video (Full Pipeline)
Navigate to: http://localhost:5000

- **Upload:** PPTX, PPT, hoặc PDF presentation
- **AI Script:** Gemini tự động tạo script cho từng slide
- **Edit:** Chỉnh sửa script nếu cần
- **Generate:** Tạo TTS audio cho từng slide
- **Create Video:** Kết hợp với SadTalker tạo video hoàn chỉnh

## 🛠️ Configuration

### Environment Variables (.env)

```bash
# Flask
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secret-key

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# GPU Settings
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=all
```

### Model Selection

**VieNeu-TTS Models:**
- `VieNeu-TTS-0.3B-q4-gguf` - CPU tối ưu, tốc độ nhanh nhất
- `VieNeu-TTS-0.3B-q8-gguf` - Cân bằng chất lượng/tốc độ
- `VieNeu-TTS-0.3B` - PyTorch 190 params, GPU accelerated
- `VieNeu-TTS` - Chất lượng tốt nhất, yêu cầu GPU mạnh

**SadTalker Settings:**
- Size: 256 (faster) hoặc 512 (better quality)
- Enhancer: gfpgan (face enhancement)
- Preprocess: full (best quality) hoặc crop (faster)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_api_routes.py

# With coverage
pytest --cov=app tests/
```

## 🐛 Troubleshooting

### GPU Not Detected
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check NVIDIA drivers
nvidia-smi
```

### Face Detection Errors
- Use clear portrait photos with visible face
- Ensure good lighting in the image
- Try different images if detection fails

### TTS Model Loading Slow
- First run downloads models from HuggingFace (may take time)
- Models are cached in `~/.cache/huggingface/`
- Use GGUF models for faster CPU inference

### Out of Memory
- Use smaller model (Q4-GGUF)
- Reduce batch size in SadTalker
- Use CPU mode: `--cpu` flag

## 📦 Docker Deployment

### Pre-built Images (GitHub Container Registry)

Tự động build và tối ưu hóa với docker-slim qua GitHub Actions CI/CD:

```bash
# Pull latest version
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest

# Run with GPU
docker run -d \
  --gpus all \
  -p 5000:5000 \
  -e GEMINI_API_KEY=your_key \
  ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest
```

**Image Tags:**
- `latest` - Latest stable release from main branch
- `develop` - Development builds
- `v1.0.0` - Semantic versioning tags
- `main-sha-<commit>` - Specific commit builds

**Image Optimization:**
- Original size: ~8.5 GB
- Optimized with docker-slim: ~3-4 GB (50-60% reduction)
- Multi-stage build với CUDA 11.8 support

📦 **[Full deployment guide →](docs/DOCKER_DEPLOYMENT.md)**

### Build from Source

See **[README.Docker.md](README.Docker.md)** for:
- GPU setup with NVIDIA Container Toolkit
- Production deployment with Docker Compose
- Development mode with live reload
- Troubleshooting and optimization
- Security best practices

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [SadTalker](https://github.com/OpenTalker/SadTalker) - Talking head generation
- [VieNeu-TTS](https://huggingface.co/pnnbao-ump) - Vietnamese TTS
- [Google Gemini](https://ai.google.dev/) - AI script generation
- [GFPGAN](https://github.com/TencentARC/GFPGAN) - Face enhancement

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Cong-ty-TNNH-MoneyEveryWhere/CreateVideo-Website/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Cong-ty-TNNH-MoneyEveryWhere/CreateVideo-Website/discussions)
- **Docker Help:** See [README.Docker.md](README.Docker.md)

---

**Made with ❤️ by MoneyEveryWhere Team**
