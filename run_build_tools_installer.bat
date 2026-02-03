@echo off
echo ========================================
echo Cai Visual Studio Build Tools
echo ========================================
echo.

set INSTALLER_PATH=%TEMP%\vs_buildtools.exe

if not exist "%INSTALLER_PATH%" (
    echo Downloading installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile '%INSTALLER_PATH%' -UseBasicParsing"
    if errorlevel 1 (
        echo Loi download!
        pause
        exit /b 1
    )
    echo Download thanh cong!
    echo.
)

echo Khoi chay installer voi quyen Administrator...
echo.
echo QUAN TRONG: Trong installer, chon:
echo   1. Tab "Workloads"
echo   2. Chon "Desktop development with C++"
echo   3. Dam bao co "MSVC v143 - VS 2022 C++ x64/x86 build tools"
echo   4. Click "Install"
echo.

powershell -Command "Start-Process -FilePath '%INSTALLER_PATH%' -Verb RunAs"

echo.
echo Installer da duoc khoi chay!
echo Vui long lam theo huong dan trong installer.
echo.
pause




