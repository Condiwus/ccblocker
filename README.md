# ccblocker —— 字幕遮挡工具

一个简单的 macOS 字幕遮挡悬浮窗工具：在你看视频时，用一块纯黑无边框窗口盖住字幕区域，逼自己先听。（基于 PyQt5）

![screenshot](screenshot.png)

## 特性

- **可拖动可拉伸的无边框悬浮窗**，总在最上层，不被其他窗口遮挡
- 🖤 **极简模式**：顶栏「收起」变成一条纯黑、可拉伸的遮挡条，双击展开

## 使用说明

1. 安装依赖并运行：
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```
   > 也可用仓库里的 `start.command` 一键启动（需先建好 venv）。
2. 顶部黑条「拖动移动」，拖窗口边缘缩放，**ESC** 关闭。
3. 点顶栏右侧「收起」进入极简遮挡条；极简下拖边缘可调大小，**双击黑条**展开。

> 注：本仓库的 `SubtitleBlocker.app` 为本地构建产物（依赖未纳入版本库的 venv），不随 git 提交；运行请使用 `main.py` 或 `start.command`。

## 快速安装方法

1. **准备 Python 环境**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt    # 安装 PyQt5
   ```
2. **运行**
   ```sh
   python main.py
   ```
