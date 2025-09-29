@echo off
title 水印文件本地应用

echo 水印文件本地应用启动中...

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境，请先安装Python 3.7或更高版本。
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b
)

REM 检查依赖是否安装
python -c "import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

echo 正在启动应用...
python code/watermark_app.py

pause