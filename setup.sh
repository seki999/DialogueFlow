#!/bin/bash
# 一键创建项目专属虚拟环境并安装依赖(macOS / Linux)
# 用法: chmod +x setup.sh && ./setup.sh

set -e
cd "$(dirname "$0")"

echo "[1/2] 创建虚拟环境 venv ..."
python3 -m venv venv

echo "[2/2] 安装依赖 ..."
source venv/bin/activate
pip install -r requirements.txt

echo
echo "完成。以后运行项目请执行 ./run.sh"
