import re
import pandas as pd

from .. import get_translation
from .. import ui

from PyQt5.QtWidgets import QTableWidget, QHBoxLayout, QComboBox, QMenu, QWidget, QLabel, QMessageBox, QVBoxLayout, QLineEdit
from PyQt5.Qt import QTableWidgetItem, QSizePolicy, QFileDialog, Qt, pyqtSignal,  QIntValidator


class TranscriptWidget(ui.PageWidget):
    analysisRequest = pyqtSignal(dict)

    def __init__(self):
        super().__init__(get_translation("ui.sub.transcript"))
        self.analysis_panel = AnalysisPanel()
        self.analysis_panel.analysisChanged.connect(self.analysis_start)
        self.analysis_panel.hide()

        # 添加面板布局
        button_layout = QHBoxLayout()
        self.import_btn = ui.PushButton(get_translation("ui.sub.transcript.import"), self)
        self.import_btn.clicked.connect(self.import_transcript)
        # self.analysis_btn = ui.PushButton(get_translation("ui.sub.transcript.analysis"), self)
        # self.analysis_btn.clicked.connect(self.analysis_grades)
        # self.select_subject = QComboBox(self)
        # self.select_subject.addItems([get_translation("sb.chinese"),get_translation("sb.english"),get_translation("sb.math"),
        #                               get_translation("sb.physics"),get_translation("sb.chemistry"),get_translation("sb.biology"),
        #                               get_translation("sb.history"),get_translation("sb.politics"),get_translation("sb.geography")])
        button_layout.addWidget(self.import_btn)
        # button_layout.addWidget(self.analysis_btn)
        self.add_layout(button_layout)

        self.transcript_table = QTableWidget()
        self.transcript_table.setHorizontalHeaderLabels([get_translation("ui.sub.transcript.filepath")])
        self.transcript_table.horizontalHeader().setStretchLastSection(True)
        self.transcript_table.setColumnCount(1)
        self.transcript_table.setAlternatingRowColors(True)
        self.transcript_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.transcript_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.transcript_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.transcript_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.transcript_table.customContextMenuRequested.connect(self.show_transcript_menu)
        self.add_widget(self.transcript_table)

    def show_transcript_menu(self, pos):
        """显示成绩单菜单"""
        menu = QMenu(self)
        menu.addAction(get_translation("ui.sub.transcript.analysis"), self.analysis_grades)
        menu.exec_(self.transcript_table.mapToGlobal(pos))

    def analysis_start(self, data: dict):
        self.analysisRequest.emit({
            "transcripts": self.transcript_table.item(self.transcript_table.currentRow(), 0).text(),
            "column": data['column'],
            "fullmarks": data['fullmarks'],
        })

    def analysis_grades(self):
        """分析成绩单"""
        self.analysis_panel.set_excel(self.transcript_table.item(self.transcript_table.currentRow(), 0).text())
        self.analysis_panel.show()

    def import_transcript(self):
        """导入成绩单"""
        file_path = QFileDialog.getOpenFileName(self, "File", "", "Excel Files (*.xlsx)")
        # 查重
        for i in range(self.transcript_table.rowCount()):
            if self.transcript_table.item(i, 0).text() == file_path[0]:
                return
        self.transcript_table.insertRow(self.transcript_table.rowCount())
        self.transcript_table.setItem(self.transcript_table.rowCount() - 1, 0, QTableWidgetItem(file_path[0]))


class AnalysisPanel(QWidget):
    # 返回用户选择的数据
    analysisChanged = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(ui.STYLESHEET)
        self.setGeometry(200, 100, 700, 500)
        self.excel_filepath: str
        self.df = None
        self.score_column = None

        self.setWindowTitle(get_translation("ui.sub.transcript.analysis.grade_analysis"))
        self.main_layout = QVBoxLayout(self)

        field_layout = QHBoxLayout()
        self.score_label = QLabel(get_translation("ui.sub.transcript.analysis.grade_field"))
        self.score_combo = QComboBox()

        self.score_combo.currentTextChanged.connect(self.score_changed)
        self.cell_input = QComboBox()
        self.cell_input.setEditable(True)

        self.confirm_cell_btn = ui.PushButton(get_translation("ui.sub.transcript.analysis.read_sheet"))
        self.confirm_cell_btn.clicked.connect(self.read_cell)

        field_layout.addWidget(self.score_label)
        field_layout.addWidget(self.score_combo)
        field_layout.addWidget(self.cell_input)
        field_layout.addWidget(self.confirm_cell_btn)

        self.main_layout.addLayout(field_layout)

        self.table = ui.ExcelTableWidget()
        self.main_layout.addWidget(self.table)

        bottom_layout = QHBoxLayout()
        # 满分
        self.max_score_input = QLineEdit()
        self.max_score_input.setPlaceholderText(get_translation("ui.sub.transcript.analysis.input_fullmarks"))
        self.max_score_input.setValidator(QIntValidator())
        self.max_score_input.setMaximumWidth(200)
        self.submit_btn = ui.PushButton(get_translation("ui.sub.transcript.analysis"))
        self.submit_btn.clicked.connect(self.emit_result)

        bottom_layout.addWidget(self.max_score_input)
        bottom_layout.addWidget(self.submit_btn)
        self.main_layout.addLayout(bottom_layout)

    def set_excel(self, filepath):
        self.excel_filepath = filepath
        self.load_excel()

    def load_excel(self):
        try:
            self.df = pd.read_excel(self.excel_filepath)
            self.show_table()
            self.init_columns()

        except Exception as e:
            QMessageBox.warning(self, get_translation("ui.error"), str(e))

    def show_table(self):
        self.table.clear()
        self.table.setRowCount(len(self.df))
        self.table.setColumnCount(len(self.df.columns))
        self.table.setHorizontalHeaderLabels(list(self.df.columns))

        for r in range(len(self.df)):
            for c in range(len(self.df.columns)):
                value = str(self.df.iloc[r,c])
                self.table.setItem(r, c, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def init_columns(self):
        self.score_combo.clear()
        keywords = [
            "总分",
            "分数",
            "成绩",
            "得分",
            "score",
            "mark",
            "grades"
        ]

        auto = None
        for col in self.df.columns:
            self.score_combo.addItem(col)
            name = str(col).lower()
            if any(k in name for k in keywords):
                auto = col

        if auto:
            self.score_combo.setCurrentText(auto)
            self.score_column = auto

    def score_changed(self,text):
        self.score_column = text

    def read_cell(self):
        cell = self.cell_input.currentText()
        result = self.cell_to_index(cell)
        if not result:
            return

        row, col = result
        try:
            self.score_column = (self.df.columns[col])
            self.score_combo.setCurrentText(self.score_column)
        except Exception:
            pass

    def cell_to_index(self,cell):
        m = re.match(r"([A-Za-z]+)(\d+)", cell)
        if not m:
            return None
        col = m.group(1).upper()
        row = int(m.group(2))

        col_num = 0
        for c in col:
            col_num = (col_num * 26 + ord(c) - 64)

        return row - 2, col_num - 1

    def emit_result(self):
        if not self.max_score_input.text().strip():
            QMessageBox.warning(self, get_translation("ui.error"), get_translation("ui.sub.transcript.analysis.input_fullmarks"))
            return
        result = {
            "column": self.score_column,
            "fullmarks": self.max_score_input.text()
        }

        self.analysisChanged.emit(result)
        self.hide()
