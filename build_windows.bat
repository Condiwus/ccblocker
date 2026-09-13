@echo off
REM ============================================================
REM  字幕遮挡工具 - Windows 一键打包脚本
REM  用法：在 Windows 上安装 Python 3.11 或 3.13 后，
REM        双击本文件，或在 cmd / PowerShell 中运行它。
REM  产物：dist\字幕遮挡工具.exe （单文件，可独立分发）
REM ============================================================
setlocal
cd /d "%~dp0"

REM 1. 创建虚拟环境（若不存在）
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

REM 2. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM 3. 打包
pyinstaller build_windows.spec

echo.
echo ============================================================
echo  打包完成！可执行文件位于：
echo  %~dp0dist\字幕遮挡工具.exe
echo ============================================================
pause
