from .. import Config
from .. import get_translation
from .. import ui

from PyQt5.QtWidgets import QTextBrowser, QSizePolicy


class DocumentsPage(ui.PageWidget):
    """文档"""

    def __init__(self):
        super().__init__(get_translation("ui.sub.documents"))

        with open(f"./libs/graphics/web/document-{Config.language}.html", "r", encoding="utf-8") as f:
            html = f.read()
            f.close()

        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        self.browser.setReadOnly(True)
        self.browser.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.browser.setHtml(html)

        layout = self.get_content_layout()
        layout.addWidget(self.browser)
