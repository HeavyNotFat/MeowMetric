from .. import get_translation
from .. import ui


class FileAnalysisWidget(ui.PageWidget):
    def __init__(self):
        super().__init__(get_translation("ui.sub.file_analysis"))
