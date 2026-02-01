# 🔧 Hướng Dẫn Cài Visual Studio Build Tools

## ⚠️ Lưu Ý:
- Cần quyền **Administrator**
- File download khoảng **3-4GB**
- Thời gian cài đặt: **10-30 phút**

## 🚀 Cách 1: Tự Động (PowerShell Script)

### Bước 1: Mở PowerShell với quyền Administrator
1. Nhấn `Win + X`
2. Chọn "Windows PowerShell (Admin)" hoặc "Terminal (Admin)"
3. Hoặc Right-click PowerShell → "Run as Administrator"

### Bước 2: Chạy script
```powershell
cd D:\CreateVideo-Website
.\install_build_tools.ps1
```

Script sẽ:
- Download Visual Studio Build Tools
- Khởi chạy installer
- Hướng dẫn chọn components

### Bước 3: Trong Installer
**QUAN TRỌNG**: Chọn:
- ✅ **Desktop development with C++** (workload)
- ✅ Đảm bảo có **MSVC v143 - VS 2022 C++ x64/x86 build tools**

### Bước 4: Sau khi cài xong
1. **Restart terminal/command prompt**
2. Cài lại VieNeu-TTS:
   ```bash
   pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
   ```

---

## 🚀 Cách 2: Thủ Công

### Bước 1: Download
Truy cập: https://visualstudio.microsoft.com/downloads/

Tìm và download: **"Build Tools for Visual Studio 2022"**

Hoặc link trực tiếp:
https://aka.ms/vs/17/release/vs_buildtools.exe

### Bước 2: Chạy Installer
1. Right-click `vs_buildtools.exe` → "Run as Administrator"
2. Chờ installer load

### Bước 3: Chọn Components
Trong installer:
1. Tab **"Workloads"**
2. Chọn **"Desktop development with C++"**
3. Đảm bảo có:
   - ✅ MSVC v143 - VS 2022 C++ x64/x86 build tools
   - ✅ Windows 10/11 SDK
   - ✅ CMake tools for Windows

4. Click **"Install"**

### Bước 4: Chờ Cài Đặt
- Thời gian: 10-30 phút
- Cần internet ổn định

### Bước 5: Restart & Test
1. **Đóng và mở lại terminal**
2. Cài lại VieNeu-TTS:
   ```bash
   pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
   ```

---

## ✅ Kiểm Tra Đã Cài Đúng:

```powershell
# Kiểm tra CMake
cmake --version

# Kiểm tra MSVC compiler
cl
```

---

## 🔄 Sau Khi Cài Build Tools:

```bash
# Cài lại VieNeu-TTS
pip install git+https://github.com/pnnbao97/VieNeu-TTS.git

# Test
python -c "from vieneu import Vieneu; print('OK')"
```

---

**Chạy script hoặc làm theo hướng dẫn thủ công! 🚀**




