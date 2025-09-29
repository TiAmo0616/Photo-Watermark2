@echo off
title 构建水印文件本地应用

echo 构建水印文件本地应用...

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境，请先安装Python 3.7或更高版本。
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b
)

REM 检查PyInstaller是否安装
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    pip install PyInstaller
)

REM 安装项目依赖
echo 正在安装项目依赖...
pip install -r requirements.txt

REM 使用PyInstaller打包
echo 正在打包为exe文件...
pyinstaller --noconfirm watermark_app.spec

echo.
echo 打包完成！可执行文件位于 dist 文件夹中。
echo.

pause