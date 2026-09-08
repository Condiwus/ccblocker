import sys
import os
import csv
from datetime import datetime

import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTextEdit, QListWidget, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPalette, QColor, QCursor, QPainter, QPen

DATA_DIR = os.path.expanduser("~/ccblocker_data")
NOTES_FILE = os.path.join(DATA_DIR, "notes.md")
VOCAB_FILE = os.path.join(DATA_DIR, "vocab.csv")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def google_translate(text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "zh-CN",
        "dt": "t",
        "q": text,
    }
    resp = requests.get(url, params=params)
    resp.encoding = 'utf-8'
    try:
        arr = resp.json()
        return arr[0][0][0]
    except Exception:
        return "翻译失败"


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

        self.label = QLabel("字幕遮挡工具 · 拖动此处移动 · ESC 退出")
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
        self.resize(520, 440)
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

        # 顶部拖动条 + 模式切换
        self.header = HeaderBar(self, on_toggle=self.toggle_minimal)
        layout.addWidget(self.header)

        # 翻译输入框
        self.input = QLineEdit()
        self.input.setPlaceholderText(
            "输入要遮挡/翻译的内容，回车翻译；拖动黑色窗口盖住字幕；ESC 退出"
        )
        layout.addWidget(self.input)
        self.input.returnPressed.connect(self.translate)

        hrow = QHBoxLayout()
        self.translate_button = QPushButton("Google翻译")
        self.translate_button.clicked.connect(self.translate)
        self.save_vocab_btn = QPushButton("＋生词本")
        self.save_vocab_btn.clicked.connect(self.save_vocab)
        hrow.addWidget(self.translate_button)
        hrow.addWidget(self.save_vocab_btn)
        layout.addLayout(hrow)

        self.output = QLabel("")
        self.output.setStyleSheet("color: lightgreen; font-weight: bold;")
        self.output.setWordWrap(True)
        layout.addWidget(self.output)

        # 生词本列表
        self.vocab_list = QListWidget()
        layout.addWidget(self.vocab_list)

        # 笔记
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("随手记笔记…（自动保存到 ~/ccblocker_data/notes.md）")
        self.notes.setMinimumHeight(80)
        layout.addWidget(self.notes)

        # 导出 / 清空
        erow = QHBoxLayout()
        self.export_btn = QPushButton("导出 Markdown")
        self.export_btn.clicked.connect(self.export_md)
        self.clear_vocab_btn = QPushButton("清空生词本")
        self.clear_vocab_btn.clicked.connect(self.clear_vocab)
        erow.addWidget(self.export_btn)
        erow.addWidget(self.clear_vocab_btn)
        layout.addLayout(erow)

        # 记录「内容区」控件，极简模式下整体收起
        self._content_widgets = [
            self.input, self.translate_button, self.save_vocab_btn,
            self.output, self.vocab_list, self.notes,
            self.export_btn, self.clear_vocab_btn,
        ]

        # 拖拽/拉伸相关
        self._drag_pos = None
        self._resize_dir = None

        # 加载已保存数据
        self.load_data()
        self.notes.textChanged.connect(self.save_notes)

    # ===== 极简模式 =====
    def toggle_minimal(self):
        if self.minimal:
            self.exit_minimal()
        else:
            self.enter_minimal()

    def enter_minimal(self):
        self.minimal = True
        self._saved_geo = self.geometry()
        for w in self._content_widgets:
            w.hide()
        # 收起为一块纯黑、可自由调节的遮挡条（隐藏顶栏与边框）
        self.header.hide()
        self.setMinimumSize(0, 0)
        self.resize(self.width(), 80)

    def exit_minimal(self):
        self.minimal = False
        self.setMinimumSize(320, 200)
        for w in self._content_widgets:
            w.show()
        self.header.show()
        self.header.set_minimal(False)
        if self._saved_geo is not None:
            self.setGeometry(self._saved_geo)
        else:
            self.resize(520, 440)

    # ===== 数据持久化 =====
    def load_data(self):
        ensure_data_dir()
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, encoding='utf-8') as f:
                self.notes.setPlainText(f.read())
        self.vocab_list.clear()
        if os.path.exists(VOCAB_FILE):
            with open(VOCAB_FILE, newline='', encoding='utf-8') as f:
                for row in csv.reader(f):
                    if len(row) >= 2:
                        self.vocab_list.addItem(f"{row[0]}  —  {row[1]}")

    def save_notes(self):
        ensure_data_dir()
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            f.write(self.notes.toPlainText())

    def save_vocab_entry(self, word, trans):
        ensure_data_dir()
        with open(VOCAB_FILE, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(
                [word, trans, datetime.now().strftime('%Y-%m-%d %H:%M')]
            )

    # ===== 功能 =====
    def translate(self):
        txt = self.input.text().strip()
        if not txt:
            self.output.setText("请输入需要翻译的内容")
            return
        self.output.setText("翻译中...")
        QApplication.processEvents()
        try:
            trans = google_translate(txt)
            self.output.setText(trans)
        except Exception:
            self.output.setText("翻译失败")

    def save_vocab(self):
        word = self.input.text().strip()
        if not word:
            self.output.setText("没有可保存的内容")
            return
        trans = self.output.text().strip()
        if trans in ("", "翻译中...", "翻译失败", "请输入需要翻译的内容"):
            trans = ""
        self.vocab_list.addItem(f"{word}  —  {trans}")
        self.save_vocab_entry(word, trans)

    def clear_vocab(self):
        self.vocab_list.clear()
        if os.path.exists(VOCAB_FILE):
            os.remove(VOCAB_FILE)

    def export_md(self):
        notes = self.notes.toPlainText().strip()
        rows = [self.vocab_list.item(i).text()
                for i in range(self.vocab_list.count())]
        md = "# 字幕遮挡工具 导出\n\n## 笔记\n\n" + (notes or "(无)") + "\n\n## 生词本\n\n"
        md += "\n".join(f"- {r}" for r in rows) if rows else "(无)"
        default = os.path.expanduser("~/Documents/ccblocker_export.md")
        path, _ = QFileDialog.getSaveFileName(
            self, "导出", default, "Markdown (*.md)"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(md)
            QMessageBox.information(self, "已导出", f"已保存到：{path}")

    def closeEvent(self, event):
        self.save_notes()
        super().closeEvent(event)

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
            # 极简模式下也允许拉伸（四边/四角可调大小）
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
        min_height = 20 if self.minimal else 200
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

    def mouseDoubleClickEvent(self, event):
        # 极简模式下双击黑条即可展开回完整模式
        if self.minimal:
            self.exit_minimal()
        super().mouseDoubleClickEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SubtitleOverlay()
    win.show()
    sys.exit(app.exec_())
