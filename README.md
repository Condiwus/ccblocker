# ccblocker —— 跨平台字幕遮挡工具

一个简单的字幕遮挡悬浮窗工具：在你看视频时，用一块无边框半透明窗口盖住字幕区域，逼自己先听。基于 PyQt5，支持 **macOS** 与 **Windows**。

## 特性

- **可拖动可拉伸的无边框悬浮窗**，总在最上层（含全屏视频之上），不被其他窗口遮挡
- 🎨 **可调颜色**：顶栏「颜色」按钮打开取色器选任意颜色；旁边黑/白/灰**预设色块**一点即换；按 **C** 在预设色间循环。选择自动保存，重启恢复
- 💧 **透明度可调 + 四角圆润**：顶栏滑块调节遮挡透明度（30%–100%），窗口四角平滑圆角
- 🖤 **极简模式**：顶栏「收起」变成一条纯色、可拉伸的遮挡条，双击展开

## 平台支持

| 平台 | 运行方式 | 全屏置顶实现 |
|---|---|---|
| macOS | `SubtitleBlocker.app` 或 `python main.py` | 原生 NSWindow 提升层级 + 允许出现在所有 Space |
| Windows | `python main.py` 或打包 `.exe` | Qt 置顶 + `user32.SetWindowPos` 强制 TOPMOST 兜底 |

> 手机（iOS / Android）版本为后续计划，本仓库目前为桌面端。

## 使用说明

### macOS

- 已构建好的 `SubtitleBlocker.app` 可直接放进 `/Applications` 双击启动；
- 或源码运行：
  ```sh
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  python main.py
  ```

### Windows

1. 安装 Python 3.13+，建虚拟环境并装依赖：
   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
2. 打包为独立 `.exe`（无需安装 Python 即可运行）：
   ```bat
   pip install pyinstaller
   pyinstaller build_windows.spec
   ```
   生成的 `dist\字幕遮挡工具.exe` 即为可分发程序（可选加图标：`pyinstaller build_windows.spec --icon app.ico`）。

## 操作速查

| 操作 | 效果 |
|---|---|
| 拖顶部黑条空白 | 移动窗口 |
| 拖窗口边缘/四角 | 缩放 |
| 顶部滑块 | 调遮挡透明度（30%–100%） |
| 点黑/白/灰 色块 | 一键换色 |
| 点「颜色」 | 取色器选任意色 |
| 按 **C** | 黑→白→灰 循环 |
| 点「收起」/ 双击黑条 | 进/出极简遮挡条 |
| **ESC** | 关闭 |

## 配置存储

颜色与透明度选择保存在 `~/ccblocker_data/config.json`，重启自动恢复。

## 备注

- 原仓库 `raysry/ccblocker` 的上游已作为 `upstream` 保留。
- `venv/`、`SubtitleBlocker.app/`（构建产物）、`ccblocker_data/`（运行时数据）均不纳入版本库。
