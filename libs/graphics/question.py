import itertools
import json

from PyQt5.QtWidgets import (
    QComboBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFrame,
)
from PyQt5.Qt import Qt, pyqtSignal, pyqtSlot, QObject, QTimer, QUrl
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .. import defer
from .. import get_translation
from .. import ui
from .. import DataMemShared

with open("./libs/graphics/web/question.html", "r", encoding="utf-8") as f:
    _chat_html = f.read()
    f.close()


class _ScrollBridge(QObject):
    """
    接收 JS 侧滚动通知，转发为 Qt 端的一次强制重绘。

    流式回复时之所以不会出现叠影，是因为每次 DOM 变化都会逼着
    Chromium 把新帧完整同步给 Qt backing store；纯滚动
    """
    def __init__(self, chat_view, parent=None):
        super().__init__(parent)
        self._chat_view = chat_view

    @pyqtSlot()
    def notify_scroll(self):
        self._chat_view.update()


class ChatView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._pending_js = []
        self._id_counter = itertools.count(1)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.page().setBackgroundColor(Qt.transparent)
        self.setContextMenuPolicy(Qt.NoContextMenu)

        self._scroll_bridge = _ScrollBridge(self)
        self._channel = QWebChannel(self.page())
        self._channel.registerObject('bridge', self._scroll_bridge)
        self.page().setWebChannel(self._channel)

        self.loadFinished.connect(self._on_load_finished)
        self.setHtml(_chat_html, QUrl("about:blank"))

    def _on_load_finished(self, ok: bool):
        self._loaded = True
        for js in self._pending_js:
            self.page().runJavaScript(js)
        self._pending_js.clear()

    def _run(self, js: str):
        if self._loaded:
            self.page().runJavaScript(js)
        else:
            self._pending_js.append(js)

    def new_id(self) -> str:
        return f"msg-{next(self._id_counter)}"

    def add_message(self, msg_id: str, text: str, is_user: bool):
        self._run(
            "addMessage(%s, %s, %s);"
            % (json.dumps(msg_id), json.dumps(text), json.dumps(bool(is_user)))
        )

    def set_message(self, msg_id: str, text: str):
        self._run("setMessage(%s, %s);" % (json.dumps(msg_id), json.dumps(text)))

    def add_thinking(self, msg_id: str):
        self._run("addThinking(%s);" % json.dumps(msg_id))


class QuestionWidget(ui.PageWidget):
    message_submitted = pyqtSignal(str)

    # 流式回复时，把多次 append 节流合并成一次渲染的间隔（毫秒）。
    _STREAM_THROTTLE_MS = 80

    def __init__(self, parent):
        super().__init__(get_translation("ui.sub.question"))
        self.parent = parent
        self.add_widget(self._build_message_area(), stretch=1)
        self.add_widget(self._build_input_area())

        # 当前正在接收流式分片的消息 id / 累积文本（None 表示空闲）
        self._streaming_id = None
        self._streaming_text = ""

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(self._STREAM_THROTTLE_MS)
        self._render_timer.timeout.connect(self._flush_streaming)

    def recv_generative_models(self, result: str):
        if self.model_combo.currentText().strip() == "Loading...": self.model_combo.clear()
        self.model_combo.addItem(result)
        DataMemShared.generative_models.append(result)
        self.parent.file_analysis_page.add_generative_models(result)

    def recv_embedding_models(self, result: str):
        DataMemShared.embedding_models.append(result)
        self.parent.setting_page.add_embedding_model(result)

    def _build_message_area(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 15%);
            }
        """)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)

        self.chat_view = ChatView(wrapper)
        layout.addWidget(self.chat_view)
        return wrapper

    def _build_input_area(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self.model_combo = QComboBox()
        self.model_combo.addItem("Loading...")
        self.model_combo.setFixedWidth(180)

        t = defer.GetModelList(self)
        t.generative_models.connect(self.recv_generative_models)
        t.embedding_models.connect(self.recv_embedding_models)
        t.start()

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText(
            get_translation("ui.sub.question.placeholder")
        )
        self.input_edit.returnPressed.connect(self._on_send)

        self.send_button = ui.PushButton(get_translation("ui.sub.question.send"))
        self.send_button.setFixedWidth(90)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self._on_send)

        row.addWidget(self.model_combo)
        row.addWidget(self.input_edit, stretch=1)
        row.addWidget(self.send_button)

        return container

    def recv_message(self, result):
        """
        流式分片回调：同一条 AI 回复的多个分片会被拼进同一个气泡里，
        而不是每个分片新建一条消息。渲染做了节流，不会每个分片都触发一次
        MathJax 排版。
        """
        chunk = str(result)
        if self._streaming_id is None:
            self._streaming_id = self.chat_view.new_id()
            self._streaming_text = ""
            self.chat_view.add_message(self._streaming_id, "", is_user=False)

        self._streaming_text += chunk
        if not self._render_timer.isActive():
            self._render_timer.start()

    def _flush_streaming(self):
        if self._streaming_id is not None:
            self.chat_view.set_message(self._streaming_id, self._streaming_text)
            self.chat_view.update()

    def finish_recv(self):
        """AI 回复全部分片接收完毕。"""
        self._flush_streaming()
        self._streaming_id = None
        self._streaming_text = ""

    def _on_send(self):
        text = self.input_edit.text().strip()
        model = self.model_combo.currentText()
        if (not text) or (not model.strip()):
            return

        t = defer.AICallBack(text, model, self)
        t.finished.connect(self.finish_recv)
        t.result.connect(self.recv_message)
        t.start()

        self.add_message(text, is_user=True)
        self.input_edit.clear()

        self._streaming_id = self.chat_view.new_id()
        self._streaming_text = ""
        self.chat_view.add_thinking(self._streaming_id)

        self.message_submitted.emit(text)

    def add_message(self, text: str, is_user: bool = False) -> str:
        """新增一条完整消息（非流式），返回消息 id，方便调用方以后想更新它。"""
        msg_id = self.chat_view.new_id()
        self.chat_view.add_message(msg_id, text, is_user)
        return msg_id
