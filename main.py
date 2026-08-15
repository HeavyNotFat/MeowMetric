import subprocess
import sys
import os
import typing
import threading

from PyQt5 import QtGui

os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu-compositing")

import libs
from libs import ui
from libs import graphics

import pandas as pd

from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import QApplication, QIcon


def read_output(stream, prefix):
    """持续读取流并打印"""
    for line in iter(stream.readline, ''):
        if line:
            print(f"[{prefix}] {line.strip()}")
    stream.close()


class MeowMetric(ui.MeowMetricProbe):
    def __init__(self):
        super().__init__()
        self.previous_scores: list | None = None
        self.setWindowTitle(libs.get_translation("ui.title"))
        self.setWindowIcon(QIcon("favicon.ico"))

        self.dashboard_page = graphics.dashborad.DashboardWidget()
        transcript_page = graphics.transcript.TranscriptWidget()
        transcript_page.analysisRequest.connect(self.start_analysis)
        self.setting_page = graphics.settings.SettingPage()
        self.file_analysis_page = graphics.file_analysis.FileAnalysisWidget()

        self.add_interface(libs.get_translation("ui.sub.dashboard"), self.dashboard_page)
        self.add_interface(libs.get_translation("ui.sub.transcript"), transcript_page)
        self.add_interface(libs.get_translation("ui.sub.question"), graphics.question.QuestionWidget(self))
        self.add_interface(libs.get_translation("ui.sub.file_analysis"), self.file_analysis_page)
        self.add_interface(libs.get_translation("ui.sub.documents"), graphics.documents.DocumentsPage(), pos="bottom")
        self.add_interface(libs.get_translation("ui.sub.settings"), self.setting_page, pos="bottom")

    def start_analysis(self, data):
        df = pd.read_excel(data['transcripts'])
        scores = (
            pd.to_numeric(df[data['column']], errors='coerce')
            .dropna()
            .tolist()
        )

        scores = [
            int(x) if x.is_integer() else x
            for x in scores
        ]
        self.dashboard_page.update_data(scores, int(data['fullmarks']), self.previous_scores)
        self.previous_scores = scores
        QMessageBox.information(self, "Info",
                                libs.get_translation("ui.analysis_done"))

    def closeEvent(self, a0: typing.Optional[QtGui.QCloseEvent]) -> None:
        llm_process.kill()
        llm_process.terminate()
        a0.accept()


if __name__ == '__main__':
    llm_process = subprocess.Popen(
        ["python", "./services/llm.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x08000000)

    # llm_process = subprocess.Popen(
    #     ["python", "./services/llm.py"],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True,
    #     creationflags=0x08000000
    # )
    # stdout_thread = threading.Thread(target=read_output, args=(llm_process.stdout, "LLM-OUT"))
    # stderr_thread = threading.Thread(target=read_output, args=(llm_process.stderr, "LLM-ERR"))
    # stdout_thread.daemon = True
    # stderr_thread.daemon = True
    # stdout_thread.start()
    # stderr_thread.start()

    app = QApplication(sys.argv)
    window = MeowMetric()
    window.show()
    app.exec_()
