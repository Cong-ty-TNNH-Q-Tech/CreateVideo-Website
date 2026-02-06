# Windows Installation Guide

## Quick Setup for Windows

### 1. Install Python 3.11
Download and install Python 3.11 from [python.org](https://www.python.org/downloads/)

### 2. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

#### Core Requirements
```powershell
pip install -r requirements.txt
```

#### Windows-Specific Requirements
```powershell
pip install -r requirements-windows.txt
```

### 4. Install PyTorch with CUDA (if you have NVIDIA GPU)
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Or CPU-only version:
```powershell
pip install torch torchvision torchaudio
```

### 5. Setup Environment Variables
Copy `.env.example` to `.env` and configure:
```powershell
copy .env.example .env
```

Edit `.env` and add your API keys:
- `GEMINI_API_KEY=your_key_here`

### 6. Run the Application
```powershell
python run.py
```

Visit `http://localhost:5000`

## Docker on Windows

If you prefer Docker:

```powershell
# Build image
docker-compose build

# Run with GPU support (requires NVIDIA Docker)
docker-compose up

# Run CPU-only
docker-compose -f docker-compose.dev.yml up
```

## Troubleshooting

### pywin32 Installation Issues
If you encounter issues with pywin32:
```powershell
pip install --upgrade pywin32
python venv/Scripts/pywin32_postinstall.py -install
```

### comtypes Issues
```powershell
pip install --upgrade comtypes
```

### CUDA/GPU Issues
Check CUDA installation:
```powershell
nvidia-smi
```

Verify PyTorch CUDA:
```python
import torch
print(torch.cuda.is_available())
```
