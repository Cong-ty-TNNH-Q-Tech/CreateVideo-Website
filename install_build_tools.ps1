# Script hướng dẫn cài Visual Studio Build Tools
# Chạy với quyền Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cài Visual Studio Build Tools" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra quyền admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Cần chạy với quyền Administrator!" -ForegroundColor Yellow
    Write-Host "Right-click PowerShell và chọn 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Hoặc chạy lệnh:" -ForegroundColor Yellow
    Write-Host "Start-Process powershell -Verb RunAs" -ForegroundColor White
    exit 1
}

Write-Host "✅ Đã có quyền Administrator" -ForegroundColor Green
Write-Host ""

# Download link
$downloadUrl = "https://aka.ms/vs/17/release/vs_buildtools.exe"
$installerPath = "$env:TEMP\vs_buildtools.exe"

Write-Host "📥 Download Visual Studio Build Tools..." -ForegroundColor Cyan
Write-Host "URL: $downloadUrl" -ForegroundColor Gray
Write-Host ""

# Download installer
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✅ Download thành công!" -ForegroundColor Green
} catch {
    Write-Host "❌ Lỗi download: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Có thể download thủ công từ:" -ForegroundColor Yellow
    Write-Host "https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "🚀 Khởi chạy installer..." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  QUAN TRỌNG: Trong installer, chọn:" -ForegroundColor Yellow
Write-Host "   - Desktop development with C++" -ForegroundColor White
Write-Host "   - Đảm bảo có 'MSVC v143 - VS 2022 C++ x64/x86 build tools'" -ForegroundColor White
Write-Host ""

# Chạy installer
Start-Process -FilePath $installerPath -Wait

Write-Host ""
Write-Host "✅ Cài đặt hoàn tất!" -ForegroundColor Green
Write-Host ""
Write-Host "Bước tiếp theo:" -ForegroundColor Cyan
Write-Host "1. Restart terminal/command prompt" -ForegroundColor White
Write-Host "2. Chạy: pip install git+https://github.com/pnnbao97/VieNeu-TTS.git" -ForegroundColor White




