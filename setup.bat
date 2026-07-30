@echo off
REM 一键创建项目专属虚拟环境并安装依赖
REM 用法:双击运行,或在命令行里执行 setup.bat

cd /d %~dp0

echo [1/2] 创建虚拟环境 venv ...
python -m venv venv
if errorlevel 1 (
    echo 创建虚拟环境失败,请确认已安装 Python 并加入了 PATH
    pause
    exit /b 1
)

echo [2/2] 安装依赖 ...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo 完成。以后运行项目请双击 run.bat
pause
