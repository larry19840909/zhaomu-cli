@echo off
REM zhaomu Admin build script
REM 1) Build React frontend
REM 2) Package with PyInstaller

echo ===== Building frontend =====
cd /d "%~dp0frontend"
call npm run build
if %ERRORLEVEL% neq 0 (
    echo Frontend build failed!
    exit /b %ERRORLEVEL%
)

echo ===== Packaging with PyInstaller =====
cd /d "%~dp0"
pyinstaller pyinstaller.spec --clean --noconfirm
if %ERRORLEVEL% neq 0 (
    echo PyInstaller build failed!
    exit /b %ERRORLEVEL%
)

echo ===== Build complete =====
echo Output: dist\zhaomu-admin\zhaomu-admin.exe
pause
