#!/bin/bash
# 激活项目专属虚拟环境并运行 main.py(macOS / Linux)
# 用法: ./run.sh

set -e
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "还没有创建虚拟环境,请先运行 ./setup.sh"
    exit 1
fi

source venv/bin/activate
python main.py
