from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from .. import ConfigLoader
from .. import Config
from .. import get_translation
from .. import ui

LANGUAGE_OPTIONS = {
    "简体中文": "zh_CN",
    "English": "us_EN"
}


class SettingPage(ui.PageWidget):
    """设置"""

    def __init__(self):
        super().__init__(get_translation("ui.sub.settings"))

        form_container = QWidget(self)
        form = QFormLayout(form_container)
        form.setSpacing(12)
        form.setContentsMargins(2, 0, 2, 0)

        # 语言设置
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGE_OPTIONS.keys())
        for name, code in LANGUAGE_OPTIONS.items():
            if code == Config.language:
                self.language_combo.setCurrentText(name)
                break
        form.addRow(
            self._label(get_translation("ui.sub.settings.language")),
            self.language_combo,
        )

        # 云端 API Base URL（OpenAI 兼容）
        self.cloud_api_base_url_edit = QLineEdit(Config.cloud_api_base_url)
        self.cloud_api_base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        form.addRow(
            self._label(get_translation("ui.sub.settings.cloud_api_base_url")),
            self.cloud_api_base_url_edit,
        )

        # 云端 API Key（OpenAI 兼容）
        self.cloud_api_key_edit = QLineEdit(Config.cloud_api_key)
        self.cloud_api_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow(
            self._label(get_translation("ui.sub.settings.cloud_api_key")),
            self.cloud_api_key_edit,
        )

        # 本地API地址
        self.model_request_line = QLineEdit(Config.model_request)
        self.model_request_line.setPlaceholderText("http://127.0.0.1:5000")
        form.addRow(
            self._label(get_translation("ui.sub.settings.local_api_url")),
            self.model_request_line,
        )

        # 嵌入模型
        self.embed_model_combo = QComboBox()
        self.embed_model_combo.addItem(Config.embed_model)
        self.embed_model_combo.setCurrentText(Config.embed_model)
        form.addRow(
            self._label(get_translation("ui.sub.settings.embed_model")),
            self.embed_model_combo,
        )

        # 保存按钮
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.save_button = ui.PushButton(get_translation("ui.sub.settings.save"))
        self.save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self.save_button)

        layout = self.get_content_layout()
        layout.addWidget(form_container)
        layout.addLayout(button_row)
        layout.addStretch(1)

    def add_embedding_model(self, model_name: str):
        self.embed_model_combo.addItem(model_name)

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size:13px; color:#7f8c8d; font-weight:bold;")
        return label

    def _on_save_clicked(self):
        selected_name = self.language_combo.currentText()
        Config["language"] = LANGUAGE_OPTIONS.get(selected_name)
        Config["cloud_api_base_url"] = self.cloud_api_base_url_edit.text().strip()
        Config["cloud_api_key"] = self.cloud_api_key_edit.text().strip()
        Config["model_request"] = self.model_request_line.text().strip()
        Config["embed_model"] = self.embed_model_combo.currentText().strip()

        try:
            ConfigLoader.save_config(Config)
        except OSError as e:
            QMessageBox.critical(self, get_translation("ui.sub.settings.save_failed"), str(e))
            return

        QMessageBox.information(self, get_translation("ui.sub.settings.save_success"), "OK!")
