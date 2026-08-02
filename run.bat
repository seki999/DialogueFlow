@echo off
REM 激活项目专属虚拟环境并运行 main.py
REM 用法:双击运行,或在命令行里执行 run.bat

cd /d %~dp0

if not exist venv (
    echo 还没有创建虚拟环境,请先运行 setup.bat
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py
pause
