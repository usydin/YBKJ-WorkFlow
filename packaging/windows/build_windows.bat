@echo off
echo ======================================================
echo   YBKJ-WorkFlow Windows Packaging Script
echo ======================================================

:: 检查是否安装了 PyInstaller
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller not found. Please install it using: pip install pyinstaller
    pause
    exit /b 1
)

:: 检查依赖是否安装
echo [INFO] Installing requirements...
pip install -r ../../requirements.txt

:: 清理旧的构建产物
echo [INFO] Cleaning old builds...
if exist build rd /s /q build
if exist dist rd /s /q dist

:: 执行打包
echo [INFO] Starting PyInstaller...
pyinstaller --clean ybkj_workflow.spec

if %errorlevel% neq 0 (
    echo [ERROR] Packaging failed.
    pause
    exit /b 1
)

echo [SUCCESS] Packaging complete. Output is in 'dist/YBKJ-WorkFlow'
echo [INFO] Running self-check on the packaged executable...
dist\YBKJ-WorkFlow\维保日报通.exe --self-check

pause
