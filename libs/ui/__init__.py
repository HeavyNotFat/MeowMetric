import typing

from PyQt5 import QtGui

from . import widgets

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QStackedWidget,
                             QGraphicsDropShadowEffect,  QAbstractItemView, QHeaderView, QTableWidget)
from PyQt5.Qt import Qt, QColor, QApplication

STYLESHEET = """
/* 全局 */
QMainWindow { background-color: transparent; }
QWidget#central_container {
    background-color: #f4f6f9;
    border-radius: 10px;
}

/* 自定义标题栏 */
#custom_titlebar {
    background-color: #2c3e50;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 0 5px;
}
#title_label {
    color: #ecf0f1;
    font-size: 13px;
    font-weight: bold;
    padding-left: 10px;
}
.titlebar-btn {
    background: transparent;
    border: none;
    color: #bdc3c7;
    font-size: 14px;
    font-weight: bold;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    border-radius: 0px;
}
.titlebar-btn:hover { 
    background-color: #34495e; 
    color: white; 
}
#btn_close:hover { 
    background-color: #e74c3c; 
    color: white; 
}

/* 侧边栏 */
#sidebar {
    background-color: #2c3e50;
    border-bottom-left-radius: 10px;
}
.nav-btn {
    text-align: left; padding: 12px 20px; color: #bdc3c7;
    border: none; font-size: 14px; border-radius: 8px; margin: 2px 8px;
}
.nav-btn:hover { background-color: #34495e; color: #ffffff; }
.nav-btn:checked { background-color: #3498db; color: #ffffff; font-weight: bold; }

/* 内容区卡片 */
.card { background-color: white; border-radius: 10px; padding: 20px; }

/* 列表 */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 12px;
    margin: 5px 0px;
    color: #2c3e50;
    font-size: 14px;
}

QListWidget::item:hover {
    background-color: #ecf5ff;
}

QListWidget::item:selected {
    background-color: #3498db;
    color: white;
}


/* 列表滚动条 */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #bdc3c7;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #95a5a6;
}

/* 操作按钮 */
.action-btn {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
}

.action-btn:hover {
    background-color: #2980b9;
}

.action-btn:pressed {
    background-color: #1f618d;
}

.action-btn.danger {
    background-color: #e74c3c;
}

.action-btn.danger:hover {
    background-color: #c0392b;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 120px;
    min-height: 28px;
    color: #2c3e50;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #3498db;
}

QComboBox:focus {
    border: 1px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    width: 25px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border-radius: 6px;
    border: 1px solid #dcdfe6;
    selection-background-color: #3498db;
    selection-color: white;
    padding: 5px;
}

/* 表格 */
QTableWidget {
    background-color: white;
    border: none;
    border-radius: 8px;
    gridline-color: #ecf0f1;
    font-size: 13px;
    color: #2c3e50;
}


QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #ecf0f1;
}


QTableWidget::item:hover {
    background-color: #ecf5ff;
}


QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}


/* 表头 */
QHeaderView::section {
    background-color: #f8f9fa;
    color: #34495e;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #dcdfe6;
    font-weight: bold;
}


/* 去掉左侧序号 */
QTableCornerButton::section {
    background-color: #f8f9fa;
}
/* 右键菜单 */
QMenu {
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 8px;
    padding: 6px;
    color: #2c3e50;
    font-size: 13px;
}


QMenu::item {
    background-color: transparent;
    padding: 8px 28px 8px 12px;
    border-radius: 6px;
    margin: 2px;
}


QMenu::item:hover {
    background-color: #3498db;
    color: white;
}


QMenu::item:selected {
    background-color: #3498db;
    color: white;
}


/* 禁用菜单项 */
QMenu::item:disabled {
    color: #bdc3c7;
}


/* 分割线 */
QMenu::separator {
    height: 1px;
    background-color: #ecf0f1;
    margin: 5px 8px;
}

/* 子菜单箭头 */
QMenu::right-arrow {
    width: 8px;
    height: 8px;
}

/* 输入框 */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 8px;
    padding: 8px 12px;
    color: #2c3e50;
    font-size: 13px;
    min-height: 28px;
}


QLineEdit:hover {
    border-color: #3498db;
}


QLineEdit:focus {
    border: 1px solid #3498db;
    background-color: #ffffff;
}


/* 禁用 */
QLineEdit:disabled {
    background-color: #f5f6fa;
    color: #bdc3c7;
}


/* Placeholder文字 */
QLineEdit {
    selection-background-color: #3498db;
    selection-color: white;
}
"""


class ExcelTableWidget(QTableWidget):
    """
    支持缩放和移动的Excel表格
    """

    def __init__(self):
        super().__init__()
        self.zoom = 100

        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        # Ctrl + 滚轮 缩放
        if modifiers == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom += 10
            else:
                self.zoom -= 10

            self.zoom = max(50, min(200, self.zoom))
            font = self.font()
            font.setPointSize(int(10 * self.zoom / 100))

            self.setFont(font)
            event.accept()
            return

        # Shift + 滚轮 横向移动
        if modifiers == Qt.ShiftModifier:
            bar = self.horizontalScrollBar()
            bar.setValue(bar.value() - event.angleDelta().y())

            event.accept()
            return

        super().wheelEvent(event)


class PushButton(QPushButton):
    """
    自定义按钮
    """
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "action-btn")


class PageWidget(QWidget):
    """
    通用页面组件基类
    继承此类可以创建自定义页面
    """
    def __init__(self, page_name: str = "", parent=None):
        super().__init__(parent)
        self.page_name = page_name

        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 25, 30, 30)
        self.main_layout.setSpacing(20)

        # 页面标题
        self.page_title = QLabel(page_name)
        self.page_title.setStyleSheet("font-size:24px; font-weight:bold; color:#2c3e50;")
        self.main_layout.addWidget(self.page_title)

        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)
        self.main_layout.addWidget(self.content_widget)

    def add_widget(self, widget: QWidget, stretch: int = 0):
        """添加组件到页面"""
        self.content_layout.addWidget(widget, stretch)

    def add_layout(self, layout, stretch: int = 0):
        """添加布局到页面"""
        self.content_layout.addLayout(layout, stretch)

    def add_stretch(self, stretch: int = 0):
        """添加弹性空间"""
        self.content_layout.addStretch(stretch)

    def get_content_layout(self) -> QVBoxLayout:
        """获取内容布局，用于直接添加组件"""
        return self.content_layout


class MeowMetricProbe(QMainWindow):
    EDGE_MARGIN = 6

    def __init__(self):
        super().__init__()
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(STYLESHEET)

        # 拖拽和调整大小状态
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None

        # 导航数据
        self._nav_items: list[tuple[str, QWidget, QPushButton]] = []  # [(text, page_widget, nav_button), ...]
        self._top_buttons: list[QPushButton] = []
        self._bottom_buttons: list[QPushButton] = []

        # 主容器
        container = QWidget()
        container.setObjectName("central_container")
        self.setCentralWidget(container)

        # 窗口阴影
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)

        # 主布局
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        self.titlebar = widgets.CustomTitleBar(self)
        main_layout.addWidget(self.titlebar)

        # 内容区域
        body = QWidget()
        self.body_layout = QHBoxLayout(body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # 侧边栏
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 10, 0, 5)
        self.sidebar_layout.setSpacing(0)
        self.sidebar_layout.setAlignment(Qt.AlignTop)

        # 页面堆栈
        self.page_stack = QStackedWidget()

        # 右侧面板
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(0)
        rp_layout.addWidget(self.page_stack)

        self.body_layout.addWidget(self.sidebar)
        self.body_layout.addWidget(right_panel, stretch=1)
        main_layout.addWidget(body)

    def add_interface(self, icon_text: str, page: PageWidget, pos: str = "top"):
        """
        添加导航项和对应页面

        :param icon_text: 导航按钮文本
        :param page: PageWidget 实例
        """
        index = len(self._nav_items)

        # 创建导航按钮
        nav_btn = QPushButton(icon_text)
        nav_btn.setProperty("class", "nav-btn")
        nav_btn.setCheckable(True)
        nav_btn.clicked.connect(lambda _, i=index: self._switch_page(i))

        if pos == "bottom":
            self._bottom_buttons.append(nav_btn)
        else:
            self._top_buttons.append(nav_btn)
        self._rebuild_sidebar()

        # 添加页面到堆栈
        self.page_stack.addWidget(page)

        # 保存引用
        self._nav_items.append((icon_text, page, nav_btn))

        # 如果是第一个页面，设置为默认
        if index == 0:
            self._switch_page(0)

    def _rebuild_sidebar(self):
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

        for btn in self._top_buttons:
            self.sidebar_layout.addWidget(btn)

        if self._bottom_buttons:
            self.sidebar_layout.addStretch(1)
            for btn in self._bottom_buttons:
                self.sidebar_layout.addWidget(btn)

    def _switch_page(self, index: int):
        """切换到指定页面"""
        if 0 <= index < len(self._nav_items):
            # 更新页面堆栈
            self.page_stack.setCurrentIndex(index)

            # 更新导航按钮状态
            for i, (_, _, btn) in enumerate(self._nav_items):
                btn.setChecked(i == index)

            # 更新标题
            page = self._nav_items[index][1]
            self.titlebar.update_title(page.page_name)

    def get_current_page(self) -> PageWidget:
        """获取当前显示的页面"""
        index = self.page_stack.currentIndex()
        if 0 <= index < len(self._nav_items):
            return self._nav_items[index][1]
        return None

    def get_page_by_index(self, index: int) -> PageWidget:
        """通过索引获取页面"""
        if 0 <= index < len(self._nav_items):
            return self._nav_items[index][1]
        return None

    def get_page_by_name(self, name: str) -> PageWidget:
        """通过页面名称获取页面"""
        for _, page, _ in self._nav_items:
            if page.page_name == name:
                return page
        return None

    def _get_resize_dir(self, pos):
        """检测鼠标是否在边缘，返回调整方向"""
        rect = self.rect()
        m = self.EDGE_MARGIN
        left = pos.x() < m
        right = pos.x() > rect.width() - m
        top = pos.y() < m
        bottom = pos.y() > rect.height() - m

        if top and left: return Qt.SizeFDiagCursor
        if top and right: return Qt.SizeBDiagCursor
        if bottom and left: return Qt.SizeBDiagCursor
        if bottom and right: return Qt.SizeFDiagCursor
        if left or right: return Qt.SizeHorCursor
        if top or bottom: return Qt.SizeVerCursor
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            resize_dir = self._get_resize_dir(event.pos())
            if resize_dir and not self.isMaximized():
                self._resizing = True
                self._resize_dir = resize_dir
                self._drag_pos = event.globalPos()
            elif event.pos().y() <= 40:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                self._resizing = False
            event.accept()

    def mouseMoveEvent(self, event):
        if not self._resizing and not self.isMaximized():
            rd = self._get_resize_dir(event.pos())
            self.setCursor(rd if rd else Qt.ArrowCursor)

        if self._resizing and self._drag_pos and not self.isMaximized():
            delta = event.globalPos() - self._drag_pos
            geo = self.geometry()
            cur = self._resize_dir

            if cur == Qt.SizeHorCursor:
                if event.pos().x() < self.EDGE_MARGIN:
                    geo.setLeft(geo.left() + delta.x())
                else:
                    geo.setRight(geo.right() + delta.x())
            elif cur == Qt.SizeVerCursor:
                if event.pos().y() < self.EDGE_MARGIN:
                    geo.setTop(geo.top() + delta.y())
                else:
                    geo.setBottom(geo.bottom() + delta.y())
            elif cur == Qt.SizeFDiagCursor:
                if event.pos().x() < self.EDGE_MARGIN:
                    geo.setLeft(geo.left() + delta.x())
                    geo.setTop(geo.top() + delta.y())
                else:
                    geo.setRight(geo.right() + delta.x())
                    geo.setBottom(geo.bottom() + delta.y())
            elif cur == Qt.SizeBDiagCursor:
                if event.pos().x() > self.width() - self.EDGE_MARGIN:
                    geo.setRight(geo.right() + delta.x())
                    geo.setTop(geo.top() + delta.y())
                else:
                    geo.setLeft(geo.left() + delta.x())
                    geo.setBottom(geo.bottom() + delta.y())

            if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                self.setGeometry(geo)
            self._drag_pos = event.globalPos()

        elif self._drag_pos and not self._resizing and event.buttons() & Qt.LeftButton:
            new_pos = event.globalPos() - self._drag_pos
            if self.isMaximized():
                old_w = self.width()
                self.showNormal()
                ratio = self.width() / old_w
                self._drag_pos.setX(int(self._drag_pos.x() * ratio))
                new_pos = event.globalPos() - self._drag_pos
            self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None
        self.setCursor(Qt.ArrowCursor)
        event.accept()


    def setWindowTitle(self, a0: typing.Optional[str]) -> None:
        self.titlebar.update_title(a0)

    def setWindowIcon(self, icon: QtGui.QIcon) -> None:
        self.titlebar.update_icon(icon)
