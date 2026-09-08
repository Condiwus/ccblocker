#!/bin/bash
# ccblocker 启动器：双击即可运行（需 macOS 已安装此 venv）
cd "$(dirname "$0")"
exec ./venv/bin/python main.py
