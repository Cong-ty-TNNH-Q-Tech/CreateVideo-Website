# Troubleshooting Guide - VideoTeaching

Hướng dẫn khắc phục các lỗi thường gặp khi cài đặt và chạy VideoTeaching.

## 📦 Installation Issues

### 1. GLIBCXX Version Mismatch (Anaconda/Conda)

**Lỗi:**
```
OSError: /opt/anaconda3/bin/../lib/libstdc++.so.6: version `GLIBCXX_3.4.30' not found
RuntimeError: Failed to load shared library 'libllama.so'
```

**Nguyên nhân:** Anaconda's `libstdc++.so.6` cũ hơn version mà llama-cpp-python CUDA build yêu cầu.

**Giải pháp:**

#### Option 1: Update Anaconda's libstdc++ (Khuyến nghị)
```bash
# Activate conda base
conda activate base

# Update libstdc++
conda install -c conda-forge libstdcxx-ng

# Recreate venv
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Option 2: Dùng System Python thay vì Anaconda
```bash
# Deactivate conda
conda deactivate

# Dùng system Python
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Option 3: Install CPU-only llama-cpp-python
```bash
# Không dùng CUDA - chỉ CPU
pip uninstall llama-cpp-python -y
pip install llama-cpp-python --force-reinstall --no-cache-dir \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

#### Option 4: Point to System libstdc++ (Temporary)
```bash
# Find system libstdc++
find /usr -name "libstdc++.so.6" 2>/dev/null

# Set LD_LIBRARY_PATH (add to ~/.bashrc for permanent)
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Restart Flask app
python run.py
```

### 2. torchvision.transforms.functional_tensor Not Found

**Lỗi:**
```
ModuleNotFoundError: No module named 'torchvision.transforms.functional_tensor'
```

**Nguyên nhân:** Torchvision version không tương thích với basicsr/gfpgan. Module `functional_tensor` đã được đổi tên trong torchvision mới.

**Giải pháp:**

```bash
# Uninstall và reinstall torchvision với đúng version
pip uninstall torchvision -y

# For CUDA 11.8 (khuyến nghị)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Hoặc chỉ định version cụ thể
pip install 'torchvision>=0.15.0,<0.20.0'

# Reinstall basicsr và gfpgan
pip install basicsr>=1.4.2 gfpgan>=1.3.8 tb-nightly
```

**Nếu gặp lỗi "Input/output error" khi install:**

```bash
# 1. Folder .venv bị corrupt - Tạo venv mới ở location khác
deactivate
cd ~
python3 -m venv ~/VideoTeaching_venv
source ~/VideoTeaching_venv/bin/activate
cd /mnt/nvme1tb/trung/VideoTeaching

# Install packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# Chạy app với venv mới
python run.py

# 2. Hoặc fix quyền truy cập folder hiện tại
sudo chown -R $USER:$USER .venv
chmod -R u+w .venv

# 3. Xóa và tạo lại .venv tại chỗ
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. llama-cpp-python Build Failed on Ubuntu/Linux

**Lỗi:**
```
/opt/anaconda3/compiler_compat/ld: warning: libgomp.so.1, needed by bin/libggml-cpu.so, not found
undefined reference to `GOMP_barrier@GOMP_1.0'
undefined reference to `GOMP_parallel@GOMP_4.0'
```

**Nguyên nhân:** Thiếu OpenMP library hoặc linker không tìm thấy `libgomp`.

**Giải pháp:**

#### Option 1: Cài đặt Pre-built Wheel (Khuyến nghị)

```bash
# Cài đặt pre-built wheel thay vì build từ source
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Nếu có GPU (CUDA):
```bash
# For CUDA 12.1
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# For CUDA 12.2
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122

# For CUDA 12.4
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

#### Option 2: Cài đặt System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    gcc \
    g++ \
    libgomp1 \
    libopenblas-dev

# Sau đó cài lại
pip install llama-cpp-python>=0.3.16
```

#### Option 3: Set CMAKE Flags

```bash
# Set environment variables trước khi install
export CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
export FORCE_CMAKE=1

pip install llama-cpp-python>=0.3.16 --no-cache-dir
```

#### Option 4: Fix Linker Path (Anaconda/Conda)

Nếu dùng Anaconda:
```bash
# Install gcc và libgomp từ conda-forge
conda install -c conda-forge gcc gxx libgomp

# Hoặc unset compiler_compat
unset LD_LIBRARY_PATH
pip install llama-cpp-python>=0.3.16
```

### 2. CUDA Out of Memory

**Lỗi:**
```
RuntimeError: CUDA out of memory
```

**Giải pháp:**

```bash
# 1. Sử dụng model nhỏ hơn
# Trong test_tts.html, chọn VieNeu-TTS-0.3B-q4-gguf thay vì q8 hoặc full

# 2. Giảm batch size trong SadTalker
# Trong video_generator.py, giảm --batch_size từ 2 xuống 1

# 3. Clear CUDA cache
python -c "import torch; torch.cuda.empty_cache()"

# 4. Force CPU mode
export CUDA_VISIBLE_DEVICES=""
```

### 3. Transformers KeyError: 'tokenizers'

**Lỗi:**
```
KeyError: 'tokenizers'
File "/venv/lib/python3.10/site-packages/transformers/__init__.py"
```

**Giải pháp:**

```bash
# Windows
Remove-Item -Recurse -Force venv\Lib\site-packages\transformers\__pycache__
Remove-Item -Recurse -Force venv\Lib\site-packages\tokenizers\__pycache__

# Linux/Mac
rm -rf venv/lib/python3.*/site-packages/transformers/__pycache__
rm -rf venv/lib/python3.*/site-packages/tokenizers/__pycache__

# Reinstall
pip install --upgrade --force-reinstall transformers tokenizers
```

### 4. Face Detection Failed - SadTalker

**Lỗi:**
```
ValueError: No face detected in the image
```

**Giải pháp:**

1. **Kiểm tra ảnh đầu vào:**
   - Sử dụng ảnh chân dung rõ nét
   - Khuôn mặt phải nhìn thấy rõ (không bị che, blur)
   - Ánh sáng tốt
   - Tránh ảnh góc nghiêng quá nhiều

2. **Code đã có multi-threshold detection:**
   ```python
   # File: app/SadTalker/src/face3d/extract_kp_videos_safe.py
   # Thử nhiều confidence threshold: 0.97, 0.92, 0.85, 0.75
   ```

3. **Nếu vẫn lỗi, thử ảnh khác hoặc resize:**
   ```bash
   # Resize ảnh về 512x512 trước khi upload
   ```

### 5. FFmpeg Not Found

**Lỗi:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Giải pháp:**

```bash
# Ubuntu/Debian
sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download từ: https://ffmpeg.org/download.html
# Hoặc dùng chocolatey:
choco install ffmpeg
```

## 🐳 Docker Issues

### 1. GPU Not Detected in Docker

**Lỗi:**
```
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

**Giải pháp:**

```bash
# 1. Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 2. Restart Docker
sudo systemctl restart docker

# 3. Test
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. Docker Build Failed - Network Issues

**Lỗi:**
```
failed to fetch metadata: failed to resolve: no such host
```

**Giải pháp:**

```bash
# 1. Set DNS in Docker
sudo nano /etc/docker/daemon.json

# Add:
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}

# 2. Restart Docker
sudo systemctl restart docker

# 3. Build with --network=host
docker build --network=host -t videoteaching .
```

### 3. Permission Denied - Docker Volumes

**Lỗi:**
```
PermissionError: [Errno 13] Permission denied: '/app/static/results'
```

**Giải pháp:**

```bash
# 1. Fix permissions on host
sudo chown -R $USER:$USER static/results static/uploads data

# 2. Hoặc thêm vào Dockerfile:
RUN chmod -R 777 /app/static/results /app/static/uploads
```

## 🔧 Runtime Issues

### 1. Flask Port Already in Use

**Lỗi:**
```
OSError: [Errno 98] Address already in use
```

**Giải pháp:**

```bash
# 1. Kill process trên port 5000
# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# 2. Hoặc đổi port trong config.py
# PORT = 8080
```

### 2. Model Download Slow/Failed

**Lỗi:**
```
HTTPError: 403 Client Error: Forbidden
ConnectionError: Failed to establish connection
```

**Giải pháp:**

```bash
# 1. Set Hugging Face token (nếu model private)
export HF_TOKEN=your_token_here

# 2. Set proxy (nếu có firewall)
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# 3. Tăng timeout
export HF_HUB_DOWNLOAD_TIMEOUT=300

# 4. Download manual
huggingface-cli download pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf
```

### 3. Gemini API Error

**Lỗi:**
```
google.api_core.exceptions.PermissionDenied: 403 API key not valid
```

**Giải pháp:**

```bash
# 1. Kiểm tra API key
echo $GEMINI_API_KEY

# 2. Tạo API key mới tại:
# https://makersuite.google.com/app/apikey

# 3. Update .env
GEMINI_API_KEY=your_new_api_key_here

# 4. Restart app
```

## 📊 Performance Issues

### 1. TTS Generation Too Slow

**Giải pháp:**

```bash
# 1. Sử dụng GGUF Q4 model (fastest)
# Trong UI chọn: VieNeu-TTS-0.3B-q4-gguf

# 2. Set threads
export OMP_NUM_THREADS=8

# 3. Nếu có GPU, dùng PyTorch model
# VieNeu-TTS-0.3B hoặc VieNeu-TTS
```

### 2. Video Generation Takes Too Long

**Giải pháp:**

```python
# Trong video_generator.py, điều chỉnh parameters:

'--size', '256',           # Giảm từ 512 → 256
'--batch_size', '1',       # Giảm batch size
'--preprocess', 'crop',    # Thay vì 'full'
# Bỏ '--enhancer', 'gfpgan'  # Skip face enhancement
```

## 🔍 Debugging Tips

### Check Library Versions

```bash
# Check GLIBCXX versions available
strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBCXX

# For Anaconda
strings /opt/anaconda3/lib/libstdc++.so.6 | grep GLIBCXX

# Check llama-cpp-python build info
python -c "import llama_cpp; print(llama_cpp.__version__)"
```

### Enable Debug Mode

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=1
```

### Check Logs

```bash
# Flask app logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f videoteaching

# System logs
journalctl -u docker -f
```

### Test Components Individually

```bash
# Test TTS
curl -X POST http://localhost:5000/api/generate-tts \
  -F "text=Xin chào" \
  -F "voice=default" \
  -F "model=pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf"

# Test SadTalker
curl -X POST http://localhost:5000/api/generate-video \
  -F "image=@test.jpg" \
  -F "audio=@test.wav"
```

## 🆘 Still Having Issues?

1. **Check System Requirements:**
   - Python 3.10+
   - CUDA 11.8+ (for GPU)
   - 8GB+ RAM (16GB recommended)
   - 10GB+ disk space

2. **Update Dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Clean Install:**
   ```bash
   # Backup data first!
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

4. **Report Issue:**
   - GitHub Issues: https://github.com/Cong-ty-TNNH-MoneyEveryWhere/CreateVideo-Website/issues
   - Include: OS, Python version, error logs, steps to reproduce

---

**Last updated:** January 28, 2026
