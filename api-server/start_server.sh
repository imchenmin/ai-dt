#!/bin/bash

# AI-DT API服务器启动脚本

set -e

echo "=== AI-DT API服务器启动脚本 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python 3.8+"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "项目根目录: $PROJECT_ROOT"
echo "API服务器目录: $SCRIPT_DIR"

# 切换到API服务器目录
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 检查配置目录
CONFIG_DIR="$PROJECT_ROOT/config"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "创建配置目录: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# 启动服务器
echo "启动API服务器..."
echo "服务器地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动uvicorn服务器
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload