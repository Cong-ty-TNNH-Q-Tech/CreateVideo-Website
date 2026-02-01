# 🔧 Fix Lỗi Cài VieNeu-TTS

## ❌ Lỗi:
```
ERROR: Failed building wheel for llama-cpp-python
CMake Error: CMAKE_C_COMPILER not set
```

## 🔍 Nguyên Nhân:

`llama-cpp-python` cần build từ source và yêu cầu:
- **CMake** (build system)
- **C++ Compiler** (Visual Studio Build Tools trên Windows)
- **Các dependencies khác**

## ✅ Giải Pháp:

### Cách 1: Cài Visual Studio Build Tools (Khuyến nghị)

1. **Download Visual Studio Build Tools:**
   - Truy cập: https://visualstudio.microsoft.com/downloads/
   - Download "Build Tools for Visual Studio"
   - Hoặc cài Visual Studio Community (có sẵn build tools)

2. **Cài đặt:**
   - Chọn "Desktop development with C++" workload
   - Đảm bảo có "MSVC v143 - VS 2022 C++ x64/x86 build tools"
   - Install

3. **Cài lại VieNeu-TTS:**
   ```bash
   pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
   ```

### Cách 2: Dùng Pre-built Wheel (Nếu có)

```bash
# Thử cài pre-built wheel
pip install llama-cpp-python --only-binary :all:
```

### Cách 3: Dùng Remote Mode (Không cần cài local)

Nếu không muốn cài build tools, có thể:
1. Deploy VieNeu-TTS trên server riêng (có GPU)
2. Dùng remote mode trong code
3. Client chỉ cần gửi request, không cần load model

### Cách 4: Skip llama-cpp-python (Nếu không cần)

Nếu VieNeu-TTS có thể chạy không cần llama-cpp-python:
```bash
# Cài VieNeu-TTS nhưng skip llama-cpp-python
pip install git+https://github.com/pnnbao97/VieNeu-TTS.git --no-deps
pip install phonemizer neucodec librosa gradio onnxruntime datasets torch torchaudio perth transformers
```

## 🧪 Test Sau Khi Cài:

```python
from vieneu import Vieneu
tts = Vieneu(mode='local')
print("VieNeu-TTS installed successfully!")
```

## ⚠️ Lưu Ý:

- **Build Tools khá nặng** (~3-4GB)
- **Remote mode** là giải pháp tốt nếu không muốn cài build tools
- **Code đã sẵn sàng**, chỉ cần VieNeu-TTS hoạt động

---

**Khuyến nghị: Cài Visual Studio Build Tools hoặc dùng Remote Mode**




