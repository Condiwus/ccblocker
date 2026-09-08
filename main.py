import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPalette, QColor, QCursor, QPainter, QPen


class HeaderBar(QWidget):
    """顶部拖动条 + 极简模式切换按钮。点击空白处移动窗口，点击按钮切换模式。"""

    def __init__(self, parent=None, on_toggle=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.on_toggle = on_toggle
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel("字幕遮挡工具 · 拖动移动 · ESC 退出")
        self.label.setStyleSheet(
            "background:#222;color:#bbb;padding-left:6px;font-size:12px;"
        )
        self.label.setFixedHeight(22)
        layout.addWidget(self.label, 1)

        self.toggle_btn = QPushButton("收起")
        self.toggle_btn.setFixedSize(44, 22)
        self.toggle_btn.setStyleSheet(
            "background:#222;color:#bbb;border:none;font-size:12px;"
            "border-left:1px solid #444;"
        )
        self.toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self.toggle_btn)

    def set_minimal(self, minimal):
        self.toggle_btn.setText("展开" if minimal else "收起")

    def _on_toggle(self):
        if self.on_toggle:
            self.on_toggle()

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

        # 不透明黑色背景
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(pal)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.setLayout(layout)

        # 顶部拖动条 + 模式切换（黑色遮挡主体由窗口黑色背景构成）
        self.header = HeaderBar(self, on_toggle=self.toggle_minimal)
        layout.addWidget(self.header)
        layout.addStretch(1)

        # 拖拽/拉伸相关
        self._drag_pos = None
        self._resize_dir = None

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
        super().paintEvent(event)
        # 极简模式下纯黑遮挡条，不绘制任何边框
        if self.minimal:
            return
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        pen1 = QPen(QColor(180, 180, 180), 2)
        pen1.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen1)
        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))
        pen2 = QPen(QColor(255, 255, 255), 1)
        pen2.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen2)
        painter.drawRect(self.rect().adjusted(3, 3, -4, -4))

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
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SubtitleOverlay()
    win.show()
    sys.exit(app.exec_())
