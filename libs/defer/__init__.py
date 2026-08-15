import json
import time

from .. import Config

from PyQt5.Qt import QThread, pyqtSignal
import requests


class AICallBack(QThread):
    result = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, question, model: str, parent=None):
        super().__init__(parent)
        self.question = question
        self.model = model

    def run(self):
        payload = {
            "query": self.question,
            "model": self.model
        }

        with requests.post(f"{Config.model_request}/api/ai/local", json=payload, stream=True) as resp:
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
                        self.result.emit(f"\n[Error] {event['data']}")
                        self.finished.emit()
                        return
                    elif event["type"] == "done":
                        print("\n[完成]")
                        self.finished.emit()
                        return
        self.finished.emit()


class AIAnalysis(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, model: str, is_local: bool, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.model = model
        self.is_local = is_local

    def run(self):
        payload = {
            "model": self.model,
            "filepath": self.file_path,
        }

        response = requests.post(f"{Config.model_request}/api/ai/{'local' if self.is_local else 'cloud'}", json=payload, stream=True)
        line = response.text
        if line.startswith("data: "):
            try:
                event = json.loads(line[len("data: "):])
            except:
                self.error.emit("Error")
                return
            if event["type"] == "error":
                self.error.emit(event["data"])
                print(f"\n[错误] {event['data']}")
        else:
            self.finished.emit(json.loads(line))


class GetModelList(QThread):
    """获取模型列表 SSE Format"""
    generative_models = pyqtSignal(str)
    embedding_models = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self) -> None:
        time.sleep(0.1)

        try:
            response = requests.post(
                f"{Config.model_request}/api/get_model_lists",
                stream=True,
                timeout=300
            )

            if response.status_code != 200:
                return

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                try:
                    event = json.loads(line[6:])
                    event_type = event.get("type")

                    if event_type == "model":
                        data = event["data"]
                        print(f"[模型] {data['name']} ({data['category']})")
                        if data['category'] == "embedding":
                            self.embedding_models.emit(data['name'])
                        else:
                            self.generative_models.emit(data['name'])

                    elif event_type == "error":
                        print(f"[错误] {event.get('data', 'Unknown error')}")

                except json.JSONDecodeError:
                    continue

        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
        except Exception as e:
            print(f"未知错误: {e}")
