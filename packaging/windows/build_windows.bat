@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "SPEC_FILE=packaging\windows\ybkj_workflow.spec"

cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo ERROR: Failed to change directory to project root.
    pause
    exit /b 1
)

echo ======================================================
echo YBKJ-WorkFlow Windows Build Script
echo ======================================================
echo PROJECT_ROOT=%CD%
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not available in PATH.
    pause
    exit /b 1
)

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Run: pip install pyinstaller
    pause
    exit /b 1
)

if not exist "%SPEC_FILE%" (
    echo ERROR: Spec file not found: %SPEC_FILE%
    pause
    exit /b 1
)

echo Cleaning build and dist directories...
if exist build rd /s /q build
if exist dist rd /s /q dist

echo Running PyInstaller...
echo python -m PyInstaller %SPEC_FILE% --noconfirm --clean
python -m PyInstaller %SPEC_FILE% --noconfirm --clean
if errorlevel 1 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo Build completed successfully.
echo DIST_PATH=%CD%\dist\YBKJ-WorkFlow
echo EXE_PATH=%CD%\dist\YBKJ-WorkFlow\YBKJ-WorkFlow.exe
echo.
echo Next commands:
echo   cd dist\YBKJ-WorkFlow
echo   YBKJ-WorkFlow.exe --version
echo   YBKJ-WorkFlow.exe --self-check
echo   YBKJ-WorkFlow.exe --no-gui-diagnose
echo.

pause
