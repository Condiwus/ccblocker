import sys
import ctypes
import ctypes.util
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QColorDialog, QSlider
)
from PyQt5.QtCore import Qt, QRect, QPoint, QRectF
from PyQt5.QtGui import QPalette, QColor, QCursor, QPainter, QPen, QPainterPath


def raise_above_fullscreen(win):
    """macOS 专属：把窗口层级提到全屏视频之上，并允许出现在所有 Space。

    Qt.WindowStaysOnTopHint 只能压过普通窗口，压不过全屏 App 所在的独立
    Space。这里直接调用原生 NSWindow API 解决。非 macOS 或无界面模式跳过。
    """
    if sys.platform != "darwin":
        return
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return  # 无界面模式下 winId() 不是 NSView，跳过原生调用
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.objc_msgSend.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        view = int(win.winId())  # QWidget.winId() 在 macOS 上是 NSView*
        sel_window = objc.sel_registerName(b"window")
        ns_win = objc.objc_msgSend(view, sel_window)
        if not ns_win:
            return

        # 允许窗口出现在所有 Space（含全屏视频所在的 Space）
        sel_behavior = objc.sel_registerName(b"setCollectionBehavior:")
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        objc.objc_msgSend(ns_win, sel_behavior, 1)  # NSWindowCollectionBehaviorCanJoinAllSpaces

        # 把层级提到全屏屏蔽窗口(CGShieldingWindowLevel)之上
        cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))
        cg.CGShieldingWindowLevel.restype = ctypes.c_int
        cg.CGShieldingWindowLevel.argtypes = []
        level = cg.CGShieldingWindowLevel()
        sel_level = objc.sel_registerName(b"setLevel:")
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
        objc.objc_msgSend(ns_win, sel_level, level + 1)
    except Exception as e:  # 失败也不影响正常使用，仅失去全屏置顶
        print("提示：无法启用全屏置顶（%s）" % e)


class HeaderBar(QWidget):
    """顶部拖动条 + 极简模式切换按钮。点击空白处移动窗口，点击按钮切换模式。"""

    def __init__(self, parent=None, on_toggle=None, on_color=None, on_preset=None,
                 on_opacity=None, opacity=100):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.on_toggle = on_toggle
        self.on_color = on_color
        self.on_preset = on_preset
        self.on_opacity = on_opacity
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel("字幕遮挡工具 · 拖动移动 · ESC 退出")
        self.label.setStyleSheet(
            "background:#222;color:#bbb;padding-left:6px;font-size:12px;"
            "border-top-left-radius:14px;"
        )
        self.label.setFixedHeight(22)
        layout.addWidget(self.label, 1)

        # 当前颜色色块
        self.swatch = QLabel()
        self.swatch.setFixedSize(16, 16)
        self.swatch.setStyleSheet(
            "background:#000;border:1px solid #555;margin:2px 4px 2px 0;"
        )
        layout.addWidget(self.swatch)

        # 常用预设色（黑 / 白 / 灰），点一下即换
        for color in (QColor("#000000"), QColor("#ffffff"), QColor("#808080")):
            b = QPushButton()
            b.setFixedSize(16, 16)
            b.setStyleSheet(
                "background:%s;border:1px solid #555;margin:2px 2px 2px 0;" % color.name()
            )
            b.clicked.connect(lambda _checked=False, c=color: self._on_preset(c))
            layout.addWidget(b)

        self.color_btn = QPushButton("颜色")
        self.color_btn.setFixedSize(40, 22)
        self.color_btn.setStyleSheet(
            "background:#222;color:#bbb;border:none;font-size:12px;"
            "border-left:1px solid #444;"
        )
        self.color_btn.clicked.connect(self._on_color)
        layout.addWidget(self.color_btn)

        # 透明度滑块（30%-100%）
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setFixedSize(70, 16)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(opacity))
        self.opacity_slider.setToolTip("遮挡透明度（越小越透明）")
        self.opacity_slider.setStyleSheet("margin:0 4px 0 0;")
        self.opacity_slider.valueChanged.connect(self._on_opacity)
        layout.addWidget(self.opacity_slider)

        self.toggle_btn = QPushButton("收起")
        self.toggle_btn.setFixedSize(44, 22)
        self.toggle_btn.setStyleSheet(
            "background:#222;color:#bbb;border:none;font-size:12px;"
            "border-left:1px solid #444;border-top-right-radius:14px;"
        )
        self.toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self.toggle_btn)

    def set_minimal(self, minimal):
        self.toggle_btn.setText("展开" if minimal else "收起")

    def set_color_swatch(self, color):
        """更新顶部色块显示当前遮挡颜色。"""
        self.swatch.setStyleSheet(
            "background:%s;border:1px solid #555;margin:2px 4px 2px 0;" % color.name()
        )

    def _on_toggle(self):
        if self.on_toggle:
            self.on_toggle()

    def _on_color(self):
        if self.on_color:
            self.on_color()

    def _on_preset(self, color):
        if self.on_preset:
            self.on_preset(color)

    def _on_opacity(self, value):
        if self.on_opacity:
            self.on_opacity(value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.window().move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class SubtitleOverlay(QWidget):
    MARGIN = 6  # 边框拉伸敏感区宽度

    def __init__(self):
        super().__init__()
        self.minimal = False
        self._saved_geo = None
        self.setWindowTitle("字幕遮挡工具")
        self.resize(560, 96)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)

        # 半透明可穿透背景（颜色 / 透明度可调，默认纯黑不透明）
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.overlay_color = QColor(0, 0, 0)
        self.opacity = 1.0
        self._load_color()
        self._apply_color()
        self.setWindowOpacity(self.opacity)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.setLayout(layout)

        # 顶部拖动条 + 颜色选择 + 预设色 + 透明度 + 模式切换
        self.header = HeaderBar(
            self, on_toggle=self.toggle_minimal, on_color=self.choose_color,
            on_preset=self.set_preset_color, on_opacity=self.set_opacity,
            opacity=self.opacity * 100
        )
        self.header.set_color_swatch(self.overlay_color)
        layout.addWidget(self.header)
        layout.addStretch(1)

        # 快捷键循环用的预设色列表（按 C 依次切换）
        self.preset_colors = [
            QColor("#000000"), QColor("#ffffff"), QColor("#808080")
        ]

        # 拖拽/拉伸相关
        self._drag_pos = None
        self._resize_dir = None

    # ===== 颜色 / 透明度 =====
    def _apply_color(self):
        self.update()  # 改色后重绘（圆角填充在 paintEvent 中完成）

    def set_opacity(self, value):
        """透明度滑块回调：value 为 30-100 的整数百分比。"""
        value = max(30, min(100, int(value)))
        self.opacity = value / 100.0
        self.setWindowOpacity(self.opacity)
        self._save_color()

    def choose_color(self):
        color = QColorDialog.getColor(
            self.overlay_color, self, "选择遮挡颜色"
        )
        if color.isValid():
            self.overlay_color = color
            self._apply_color()
            self.header.set_color_swatch(color)
            self._save_color()

    def _config_path(self):
        base = os.path.expanduser("~/ccblocker_data")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "config.json")

    def _load_color(self):
        try:
            p = self._config_path()
            if os.path.exists(p):
                with open(p) as f:
                    d = json.load(f)
                if d.get("color"):
                    c = QColor(d["color"])
                    if c.isValid():
                        self.overlay_color = c
                if "opacity" in d:
                    try:
                        self.opacity = max(0.3, min(1.0, float(d["opacity"])))
                    except Exception:
                        self.opacity = 1.0
        except Exception:
            pass

    def _save_color(self):
        try:
            with open(self._config_path(), "w") as f:
                json.dump(
                    {"color": self.overlay_color.name(), "opacity": round(self.opacity, 2)},
                    f,
                )
        except Exception:
            pass

    def set_preset_color(self, color):
        """点击预设色块或按 C 循环时调用，立即换色并保存。"""
        self.overlay_color = QColor(color)
        self._apply_color()
        self.header.set_color_swatch(self.overlay_color)
        self._save_color()

    def _cycle_preset(self):
        """按 C 在预设色（黑→白→灰→黑）之间循环。"""
        names = [c.name().lower() for c in self.preset_colors]
        cur = self.overlay_color.name().lower()
        idx = (names.index(cur) + 1) % len(self.preset_colors) if cur in names else 0
        self.set_preset_color(self.preset_colors[idx])

    # ===== 极简模式 =====
    def toggle_minimal(self):
        if self.minimal:
            self.exit_minimal()
        else:
            self.enter_minimal()

    def enter_minimal(self):
        self.minimal = True
        self._saved_geo = self.geometry()
        self.header.hide()
        # 收起为一块纯黑、可自由调节的遮挡条（隐藏顶栏与边框）
        self.setMinimumSize(0, 0)

    def exit_minimal(self):
        self.minimal = False
        self.setMinimumSize(320, 60)
        self.header.show()
        self.header.set_minimal(False)
        if self._saved_geo is not None:
            self.setGeometry(self._saved_geo)
        else:
            self.resize(560, 96)

    # === 无边框窗体的移动与拉伸 ===
    def paintEvent(self, event):
        # 用圆角矩形填充遮挡区，四角圆润；透明度由窗口整体 opacity 控制
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        r = self.rect()
        radius = min(14, r.height() // 2)
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), radius, radius)
        painter.fillPath(path, QColor(self.overlay_color))
        if not self.minimal:
            # 完整模式下画一圈浅色描边，方便看清边界
            pen = QPen(QColor(180, 180, 180, 200), 2)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            self._resize_dir = self._get_resize_dir(pos)
            if not self._resize_dir:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self._resize_dir:
            self._do_resize(event.globalPos())
        elif self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
        else:
            self._update_cursor(pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_dir = None
        self._update_cursor(event.pos())
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # 极简模式下双击黑条即可展开回完整模式
        if self.minimal:
            self.exit_minimal()
        super().mouseDoubleClickEvent(event)

    def _get_resize_dir(self, pos):
        rect = self.rect()
        x, y, w, h = pos.x(), pos.y(), rect.width(), rect.height()
        margins = self.MARGIN
        left = x <= margins
        right = x >= w - margins
        top = y <= margins
        bottom = y >= h - margins
        if left and top:
            return "top_left"
        if right and top:
            return "top_right"
        if left and bottom:
            return "bottom_left"
        if right and bottom:
            return "bottom_right"
        if top:
            return "top"
        if left:
            return "left"
        if right:
            return "right"
        if bottom:
            return "bottom"
        return None

    def _do_resize(self, global_pos):
        rect = self.geometry()
        min_width = 100 if self.minimal else 320
        min_height = 20 if self.minimal else 60
        if self._resize_dir == "left":
            diff = global_pos.x() - rect.left()
            if rect.width() - diff >= min_width:
                rect.setLeft(rect.left() + diff)
        elif self._resize_dir == "right":
            diff = global_pos.x() - rect.right()
            if rect.width() + diff >= min_width:
                rect.setRight(rect.right() + diff)
        elif self._resize_dir == "top":
            diff = global_pos.y() - rect.top()
            if rect.height() - diff >= min_height:
                rect.setTop(rect.top() + diff)
        elif self._resize_dir == "bottom":
            diff = global_pos.y() - rect.bottom()
            if rect.height() + diff >= min_height:
                rect.setBottom(rect.bottom() + diff)
        elif self._resize_dir == "top_left":
            diff_x = global_pos.x() - rect.left()
            diff_y = global_pos.y() - rect.top()
            if rect.width() - diff_x >= min_width:
                rect.setLeft(rect.left() + diff_x)
            if rect.height() - diff_y >= min_height:
                rect.setTop(rect.top() + diff_y)
        elif self._resize_dir == "top_right":
            diff_x = global_pos.x() - rect.right()
            diff_y = global_pos.y() - rect.top()
            if rect.width() + diff_x >= min_width:
                rect.setRight(rect.right() + diff_x)
            if rect.height() - diff_y >= min_height:
                rect.setTop(rect.top() + diff_y)
        elif self._resize_dir == "bottom_left":
            diff_x = global_pos.x() - rect.left()
            diff_y = global_pos.y() - rect.bottom()
            if rect.width() - diff_x >= min_width:
                rect.setLeft(rect.left() + diff_x)
            if rect.height() + diff_y >= min_height:
                rect.setBottom(rect.bottom() + diff_y)
        elif self._resize_dir == "bottom_right":
            diff_x = global_pos.x() - rect.right()
            diff_y = global_pos.y() - rect.bottom()
            if rect.width() + diff_x >= min_width:
                rect.setRight(rect.right() + diff_x)
            if rect.height() + diff_y >= min_height:
                rect.setBottom(rect.bottom() + diff_y)
        self.setGeometry(rect)

    def _update_cursor(self, pos):
        cursor = Qt.ArrowCursor
        dir_ = self._get_resize_dir(pos)
        if dir_ in ["left", "right"]:
            cursor = Qt.SizeHorCursor
        elif dir_ in ["top", "bottom"]:
            cursor = Qt.SizeVerCursor
        elif dir_ in ["top_left", "bottom_right"]:
            cursor = Qt.SizeFDiagCursor
        elif dir_ in ["top_right", "bottom_left"]:
            cursor = Qt.SizeBDiagCursor
        self.setCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_C:
            self._cycle_preset()
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SubtitleOverlay()
    win.show()
    raise_above_fullscreen(win)  # 全屏视频之上仍置顶
    sys.exit(app.exec_())
