from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap


class CustomTitleBar(QFrame):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("custom_titlebar")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(8)

        # 窗口图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)

        pixmap = QPixmap()
        self.icon_label.setPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        layout.addWidget(self.icon_label)

        # 标题
        self.title_label = QLabel("学喵探针")
        self.title_label.setObjectName("title_label")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # 最小化
        btn_min = QPushButton("—")
        btn_min.setProperty("class", "titlebar-btn")
        btn_min.setFlat(True)
        btn_min.clicked.connect(parent_window.showMinimized)

        # 最大化
        btn_max = QPushButton("□")
        btn_max.setProperty("class", "titlebar-btn")
        btn_max.setFlat(True)
        btn_max.clicked.connect(self.toggle_maximize)

        # 关闭
        btn_close = QPushButton("✕")
        btn_close.setObjectName("btn_close")
        btn_close.setProperty("class", "titlebar-btn")
        btn_close.setFlat(True)
        btn_close.clicked.connect(parent_window.close)

        layout.addWidget(btn_min)
        layout.addWidget(btn_max)
        layout.addWidget(btn_close)

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def update_title(self, text):
        self.title_label.setText("学喵探针")

    def update_icon(self, icon):
        pixmap = icon.pixmap(24, 24)

        self.icon_label.setPixmap(
            pixmap.scaled(
                24,
                24,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
