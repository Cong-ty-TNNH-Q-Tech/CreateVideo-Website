# ⚡ Cài Visual Studio Build Tools - Hướng Dẫn Nhanh

## ✅ Đã Download Installer!

File installer đã được download tại:
```
C:\Users\Admin\AppData\Local\Temp\vs_buildtools.exe
```

## 🚀 Cách Chạy:

### Cách 1: Chạy File Batch (Dễ nhất)
1. Double-click file: `run_build_tools_installer.bat`
2. Cho phép quyền Administrator khi được hỏi
3. Làm theo hướng dẫn trong installer

### Cách 2: Chạy Thủ Công
1. Mở File Explorer
2. Đi đến: `C:\Users\Admin\AppData\Local\Temp\`
3. Tìm file `vs_buildtools.exe`
4. Right-click → "Run as Administrator"
5. Cho phép UAC prompt

### Cách 3: PowerShell Command
```powershell
Start-Process "$env:TEMP\vs_buildtools.exe" -Verb RunAs
```

## 📋 Trong Installer - QUAN TRỌNG:

1. **Tab "Workloads"** (bên trái)
2. Chọn **"Desktop development with C++"** ✅
3. Đảm bảo có:
   - ✅ MSVC v143 - VS 2022 C++ x64/x86 build tools
   - ✅ Windows 10/11 SDK
   - ✅ CMake tools for Windows
4. Click **"Install"** (góc dưới bên phải)

## ⏱️ Thời Gian:
- Download: Đã xong ✅
- Cài đặt: 10-30 phút (tùy internet)

## ✅ Sau Khi Cài Xong:

1. **Đóng và mở lại terminal**
2. Cài lại VieNeu-TTS:
   ```bash
   pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
   ```

---

**Chạy file `run_build_tools_installer.bat` để bắt đầu! 🚀**




