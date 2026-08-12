import json
import requests

from PyQt5.Qt import QThread, pyqtSignal

URL_STREAM = "http://localhost:5000/api/ai/stream"


class AICallBack(QThread):
    result = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.question = question

    def run(self):
        payload = {
            "query": self.question,
        }

        with requests.post(URL_STREAM, json=payload, stream=True) as resp:
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    event = json.loads(line[len("data: "):])
                    if event["type"] == "content":
                        self.result.emit(event["data"])
                    elif event["type"] == "status":
                        print(f"[状态] {event['data']}")
                    elif event["type"] == "error":
                        print(f"\n[错误] {event['data']}")
                        self.finished.emit()
                        return
                    elif event["type"] == "done":
                        print("\n[完成]")
                        self.finished.emit()
                        return
        self.finished.emit()

