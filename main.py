import subprocess

import libs
from libs import ui
from libs import graphics

import pandas as pd

from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import QApplication, QIcon


class MeowMetric(ui.MeowMetricProbe):
    def __init__(self):
        super().__init__()
        self.previous_scores: list | None = None
        self.setWindowTitle(libs.get_translation("ui.title"))
        self.setWindowIcon(QIcon("favicon.ico"))

        self.dashboard_page = graphics.dashborad.DashboardWidget()
        transcript_page = graphics.transcript.TranscriptWidget()
        transcript_page.analysisRequest.connect(self.start_analysis)

        self.add_interface(libs.get_translation("ui.sub.dashboard"), self.dashboard_page)
        self.add_interface(libs.get_translation("ui.sub.transcript"), transcript_page)
        self.add_interface(libs.get_translation("ui.sub.question"), graphics.question.QuestionWidget())
        self.add_interface(libs.get_translation("ui.sub.file_analysis"), graphics.file_analysis.FileAnalysisWidget())


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


if __name__ == '__main__':
    process = subprocess.Popen(
        ["python", "./services/llm.py", "-n", "10"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x08000000
    )

    app = QApplication([])
    window = MeowMetric()
    window.show()
    app.exec_()
