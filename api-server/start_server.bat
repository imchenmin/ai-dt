@echo off
chcp 65001 >nul

echo === AI-DT API服务器启动脚本 ===

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\

echo 项目根目录: %PROJECT_ROOT%
echo API服务器目录: %SCRIPT_DIR%

REM 切换到API服务器目录
cd /d "%SCRIPT_DIR%"

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 设置环境变量
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%

REM 检查配置目录
set CONFIG_DIR=%PROJECT_ROOT%config
if not exist "%CONFIG_DIR%" (
    echo 创建配置目录: %CONFIG_DIR%
    mkdir "%CONFIG_DIR%"
)

REM 启动服务器
echo 启动API服务器...
echo 服务器地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动uvicorn服务器
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause