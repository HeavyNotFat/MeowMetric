from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QComboBox, QTextEdit, QListWidget,
    QListWidgetItem,
    QProgressBar, QFileDialog,
    QSplitter,
    QMessageBox,
)

from .. import Config
from .. import get_translation, DataMemShared
from .. import ui
from .. import defer


class FileAnalysisWidget(ui.PageWidget):
    """
    AI 试卷分析页面
    """

    def __init__(self):
        super().__init__(get_translation("ui.sub.file_analysis"))

        self.cache_analysis = {}

        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        file_card = QGroupBox(get_translation("ui.sub.file_analysis.paper"))
        file_layout = QVBoxLayout(file_card)
        file_layout.setSpacing(12)

        description = QLabel(get_translation("ui.sub.file_analysis.desc"))
        description.setWordWrap(True)
        description.setStyleSheet(
            "color: #7f8c8d; font-size: 13px;"
        )

        file_row = QHBoxLayout()

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText(get_translation("ui.sub.file_analysis.select_file_holder"))
        self.file_path_edit.setReadOnly(True)

        self.select_file_btn = QPushButton(get_translation("ui.sub.file_analysis.choose"))
        self.select_file_btn.setProperty("class", "action-btn")

        file_row.addWidget(self.file_path_edit, 1)
        file_row.addWidget(self.select_file_btn)

        self.file_info_label = QLabel(get_translation("ui.sub.file_analysis.non-chosen_file"))
        self.file_info_label.setStyleSheet(
            "color: #95a5a6; font-size: 12px;"
        )

        file_layout.addWidget(description)
        file_layout.addLayout(file_row)
        file_layout.addWidget(self.file_info_label)
        file_layout.addStretch()

        config_card = QGroupBox(get_translation("ui.sub.file_analysis.ai_config"))
        config_layout = QVBoxLayout(config_card)
        config_layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            get_translation("ui.sub.file_analysis.local_ai"),
            get_translation("ui.sub.file_analysis.cloud_ai"),
        ])
        self.model_combo.setCurrentIndex(1)

        form_layout.addRow(get_translation("ui.sub.file_analysis.ai_model"), self.model_combo)

        # 本地模型：下拉选择；云端模型：手动输入模型名字
        self.local_model_label = QLabel(get_translation("ui.sub.file_analysis.local_model_name"))
        self.local_model_combo = QComboBox()

        self.cloud_model_label = QLabel(get_translation("ui.sub.file_analysis.cloud_model_name"))
        self.cloud_model_edit = QLineEdit()
        self.cloud_model_edit.setText(Config.cloud_model)
        self.cloud_model_edit.textChanged.connect(self.cloud_model_textChanged)
        self.cloud_model_edit.setPlaceholderText(
            get_translation("ui.sub.file_analysis.cloud_model_holder")
        )

        form_layout.addRow(self.local_model_label, self.local_model_combo)
        form_layout.addRow(self.cloud_model_label, self.cloud_model_edit)

        config_layout.addLayout(form_layout)

        self.start_analysis_btn = QPushButton(get_translation("ui.sub.file_analysis.start_analysis"))
        self.start_analysis_btn.setProperty("class", "action-btn")
        self.start_analysis_btn.setMinimumHeight(38)

        config_layout.addWidget(self.start_analysis_btn)

        top_layout.addWidget(file_card, 1)
        top_layout.addWidget(config_card, 1)

        self.add_layout(top_layout)

        progress_card = QGroupBox(get_translation("ui.sub.file_analysis.progress"))
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setSpacing(8)

        progress_top = QHBoxLayout()

        self.progress_status = QLabel(get_translation("ui.sub.file_analysis.waiting"))
        self.progress_status.setStyleSheet(
            "font-weight: bold; color: #2c3e50;"
        )

        self.progress_percent = QLabel("0%")
        self.progress_percent.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        progress_top.addWidget(self.progress_status)
        progress_top.addStretch()
        progress_top.addWidget(self.progress_percent)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        progress_layout.addLayout(progress_top)
        progress_layout.addWidget(self.progress_bar)

        self.add_widget(progress_card)

        result_card = QGroupBox(get_translation("ui.sub.file_analysis.ai_analysis_result"))
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(10, 10, 10, 10)

        result_splitter = QSplitter(Qt.Horizontal)

        question_panel = QWidget()
        question_layout = QVBoxLayout(question_panel)
        question_layout.setContentsMargins(0, 0, 0, 0)

        question_title = QLabel(get_translation("ui.sub.file_analysis.file_sb"))
        question_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2c3e50;"
        )

        self.question_list = QListWidget()

        question_layout.addWidget(question_title)
        question_layout.addWidget(self.question_list)

        result_splitter.addWidget(question_panel)

        result_panel = QWidget()
        result_panel_layout = QVBoxLayout(result_panel)
        result_panel_layout.setContentsMargins(0, 0, 0, 0)
        result_panel_layout.setSpacing(10)

        summary_title = QLabel(get_translation("ui.sub.file_analysis.ai_ess"))
        summary_title.setStyleSheet(
            "font-size: 14px;"
            "font-weight: bold;"
            "color: #2c3e50;"
        )

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlainText(get_translation("ui.sub.file_analysis.analysis_tips"))

        result_panel_layout.addWidget(summary_title)
        result_panel_layout.addWidget(
            self.analysis_text,
            1,
        )

        result_splitter.addWidget(result_panel)

        # 左右宽度比例
        result_splitter.setStretchFactor(0, 1)
        result_splitter.setStretchFactor(1, 4)

        result_layout.addWidget(result_splitter)

        self.add_widget(result_card, 1)

        self._connect_signals()

        # 根据当前 AI 类型初始化模型选择控件的显隐
        self._on_model_type_changed(self.model_combo.currentIndex())

    def cloud_model_textChanged(self, text):
        Config.cloud_model = text
        Config.save()

    def add_generative_models(self, result: str):
        self.local_model_combo.addItem(result)

    def add_question_item(self, session: str, type_: str):
        self.question_list.addItem(QListWidgetItem(f"{session}  {type_}"))

    def _connect_signals(self):
        self.select_file_btn.clicked.connect(
            self._select_file
        )

        self.start_analysis_btn.clicked.connect(self._start_analysis)

        self.question_list.currentRowChanged.connect(self._on_question_selected)

        self.model_combo.currentIndexChanged.connect(self._on_model_type_changed)

    def _on_model_type_changed(self, index: int):
        """
        index == 0 -> 本地模型（下拉选择）
        index == 1 -> 云端模型（手动输入模型名字）
        """
        is_local = index == 0

        self.local_model_label.setVisible(is_local)
        self.local_model_combo.setVisible(is_local)

        self.cloud_model_label.setVisible(not is_local)
        self.cloud_model_edit.setVisible(not is_local)

    def _current_model_name(self) -> str:
        if self.model_combo.currentIndex() == 0:
            return self.local_model_combo.currentText().strip()
        return self.cloud_model_edit.text().strip()

    def _select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            get_translation("ui.sub.file_analysis.choose"),
            "",
            (
                "Files (*.png *.jpg *.jpeg);;"
                "Images (*.png *.jpg *.jpeg);;"
                "All Files (*)"
            ),
        )

        if not file_path:
            return

        self.file_path_edit.setText(file_path)

        file_name = file_path.split("/")[-1]

        self.file_info_label.setText(
            f"{get_translation("ui.sub.file_analysis.choose")}：{file_name}"
        )

        self.progress_status.setText(get_translation("ui.sub.file_analysis.file_ok"))

        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")

    def _start_analysis(self):
        is_local = self.model_combo.currentIndex() == 0

        self.question_list.clear()
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(
                self,
                "Error",
                get_translation("ui.sub.file_analysis.one_file_required"),
            )
            return

        model_name = self._current_model_name()
        if self.model_combo.currentIndex() == 1 and not model_name:
            QMessageBox.warning(
                self,
                "Error",
                get_translation("ui.sub.file_analysis.model_name_required"),
            )
            return

        t = defer.AIAnalysis(file_path, model_name, is_local, self)
        t.finished.connect(self._on_analysis_finished)
        t.error.connect(self._on_analysis_error)
        t.start()

        self.progress_status.setText(get_translation("ui.sub.file_analysis.analysing"))
        self.progress_bar.setValue(25)
        self.progress_percent.setText("25%")
        self.analysis_text.setPlainText(get_translation("ui.sub.file_analysis.analysing"))
        self.start_analysis_btn.setEnabled(False)

    def _on_question_selected(self, row: int):
        if row < 0:
            return

        question_number = row + 1
        key = f"label{question_number}"
        if key not in self.cache_analysis:
            key = str(question_number)
        data = self.cache_analysis[key]
        self.analysis_text.setPlainText(
            f"{question_number}\n\n"
            f"「{get_translation('ui.sub.file_analysis.point')}」\n"
            f"{data['point']}\n\n"
            f"「{get_translation('ui.sub.file_analysis.difficulty')}」\n"
            f"{data['difficulty']}\n\n"
            f"「{get_translation('ui.sub.file_analysis.correction')}」\n"
            f"{"✅" if data['correct'] is True else "❌" if data['correct'] is False else get_translation('ui.sub.file_analysis.no_answer')}\n\n"
            f"「{get_translation('ui.sub.file_analysis.comment')}」\n"
            f"{data['comment']}"
        )

    def _on_analysis_error(self, _):
        self.progress_status.setText(get_translation("ui.sub.file_analysis.analysis_finished"))
        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")
        self.start_analysis_btn.setEnabled(True)

    def _on_analysis_finished(self, data: dict):
        self.progress_status.setText(get_translation("ui.sub.file_analysis.analysis_finished"))
        self.progress_bar.setValue(100)
        self.progress_percent.setText("100%")

        self.cache_analysis = data
        for label, analysis in data.items():
            self.add_question_item(f"第{list(data.keys()).index(label) + 1}题", analysis["type"])
        self.start_analysis_btn.setEnabled(True)