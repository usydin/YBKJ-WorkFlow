@echo off
setlocal enabledelayedexpansion

echo ======================================================
echo   友邦维保工作流系统 (YBKJ-WorkFlow) Windows 打包脚本
echo ======================================================

:: 设置项目根目录 (当前脚本在 packaging\windows\，向上两级)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."
set "PROJECT_ROOT=%cd%"

echo [信息] 项目根目录: %PROJECT_ROOT%
echo [信息] 脚本目录: %SCRIPT_DIR%

:: 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请确保 Python 已安装并添加到系统变量 PATH 中。
    pause
    exit /b 1
)

:: 2. 检查 PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未找到 PyInstaller，请执行以下命令安装:
    echo        pip install pyinstaller
    pause
    exit /b 1
)

:: 3. 检查依赖
echo [信息] 正在检查/安装项目依赖...
pip install -r requirements.txt

:: 4. 检查 Spec 文件
set "SPEC_FILE=packaging\windows\ybkj_workflow.spec"
if not exist "%SPEC_FILE%" (
    echo [错误] 找不到 Spec 文件: %SPEC_FILE%
    pause
    exit /b 1
)

:: 5. 清理旧产物
echo [信息] 正在清理旧的构建产物 (build, dist)...
if exist build rd /s /q build
if exist dist rd /s /q dist

:: 6. 执行打包
echo [信息] 正在启动 PyInstaller 打包流程...
echo [执行] pyinstaller --clean "%SPEC_FILE%"
pyinstaller --clean "%SPEC_FILE%"

if %errorlevel% neq 0 (
    echo [错误] 打包失败，请检查上方错误输出。
    pause
    exit /b 1
)

:: 7. 输出结果
echo.
echo ======================================================
echo [成功] 打包完成！
echo ======================================================
echo [产物位置] %PROJECT_ROOT%\dist\YBKJ-WorkFlow
echo [可执行文件] 维保日报通.exe (或 YBKJ-WorkFlow.exe)
echo.
echo [测试建议] 请依次执行以下命令进行自检:
echo    1. cd dist\YBKJ-WorkFlow
echo    2. 维保日报通.exe --version
echo    3. 维保日报通.exe --self-check
echo    4. 维保日报通.exe --no-gui-diagnose
echo.
echo [提示] 建议参考 docs\WINDOWS_BUILD_TEST_RECORD.md 进行测试记录。
echo ======================================================

pause
