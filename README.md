# ccblocker —— 字幕遮挡翻译工具

一个简单的字幕遮挡与机器翻译悬浮窗工具，适用于视频字幕自助遮挡和一键翻译辅助。（适配 macOS，基于 PyQt5 与 Google Translate API）

![screenshot](screenshot.png)

## 特性

- **可拖动可拉伸的无边框悬浮窗**，总在最上层，不被其他窗口遮挡
- **回车键直接自动翻译（调用 Google 翻译）**
- 📝 **随手笔记**：自动保存到 `~/ccblocker_data/notes.md`
- 📚 **生词本**：翻译后一键收藏，可导出 Markdown 到 `~/Documents`
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
2. 顶部黑条「拖动此处移动」，拖窗口边缘缩放，**ESC** 关闭。
3. 点顶栏右侧「收起」进入极简遮挡条；极简下拖边缘可调大小，**双击黑条**展开。
4. 翻译走 Google 翻译，国内网络可能需要代理 / VPN。

> 注：本仓库的 `SubtitleBlocker.app` 为本地构建产物（依赖未纳入版本库的 venv），不随 git 提交；运行请使用 `main.py` 或 `start.command`。


## 快速安装方法

1. **准备 Python 环境**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt    # 或手动安装 PyQt5 requests