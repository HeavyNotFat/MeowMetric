import itertools
import json

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt5.Qt import QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .. import defer
from .. import get_translation
from .. import ui


_MATHJAX_SRC = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"

_CHAT_HTML = r"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
            },
            svg: { fontCache: 'global' },
            startup: {
                pageReady() {
                    return MathJax.startup.defaultPageReady().then(function () {
                        window.dispatchEvent(new Event('MathJaxReady'));
                });
            }
        }
    };
    </script>
    <script src="mathjax_src" id="MathJax-script" async></script>
    <style>
    html, body {
        margin: 0;
        padding: 0;
        height: 100%;
        background: transparent;
        font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif;
        font-size: 13px;
        overflow: hidden;
    }
    #container {
        height: 100vh;
        box-sizing: border-box;
        padding: 16px;
        display: flex;
        flex-direction: column;
        overflow-y: auto;
        transform: translateZ(0);
        will-change: transform;
        hange: transform;
    }
    .row {
        display: flex;
        margin: 4px 0;
        }
    .row.user { justify-content: flex-end; }
    .row.ai { justify-content: flex-start; }
    
    .bubble {
        max-width: 480px;
        padding: 10px 14px;
        border-radius: 10px;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.5;
    }
    .bubble.user {
        background-color: #3498db;
        color: #ffffff;
        }
    .bubble.ai {
        background-color: #ffffff;
        border: 1px solid #ecf0f1;
        color: #2c3e50;
    }
    .bubble code, .bubble pre {
        background: rgba(0, 0, 0, 0.06);
        border-radius: 4px;
        padding: 1px 4px;
        font-family: Consolas, "Courier New", monospace;
    }
    .bubble.thinking {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 14px 16px;
    }
    .bubble.thinking .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #bdc3c7;
        animation: thinking-bounce 1.4s infinite ease-in-out both;
    }
    .bubble.thinking .dot:nth-child(1) { animation-delay: -0.32s; }
    .bubble.thinking .dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes thinking-bounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    :-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.15);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-track { background: transparent; }
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
    var container = document.getElementById('container');

    function escapeHtml(s) {
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }
    
    function scrollToBottom() {
        container.scrollTop = container.scrollHeight;
    }
    
    function typesetAndScroll(el) {
        if (window.MathJax && window.MathJax.typesetPromise) {
            MathJax.typesetPromise([el]).then(scrollToBottom).catch(scrollToBottom);
        } else {
            window.addEventListener('MathJaxReady', function once() {
            window.removeEventListener('MathJaxReady', once);
            MathJax.typesetPromise([el]).then(scrollToBottom).catch(scrollToBottom);
        });
            scrollToBottom();
        }
    }

    function addThinking(id) {
        var row = document.createElement('div');
        row.className = 'row ai';
        
        var bubble = document.createElement('div');
        bubble.id = id;
        bubble.className = 'bubble ai thinking';
        bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        
        row.appendChild(bubble);
        container.appendChild(row);
        scrollToBottom();
    }
        
    function setMessage(id, text) {
        var bubble = document.getElementById(id);
        if (!bubble) { return; }
        bubble.classList.remove('thinking');
        bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
        typesetAndScroll(bubble);
    }
        
    function addMessage(id, text, isUser) {
        var row = document.createElement('div');
        row.className = 'row ' + (isUser ? 'user' : 'ai');
        
        var bubble = document.createElement('div');
        bubble.id = id;
        bubble.className = 'bubble ' + (isUser ? 'user' : 'ai');
        bubble.innerHTML = escapeHtml(text).replace(/\\n/g, '<br>');
        
        row.appendChild(bubble);
        container.appendChild(row);
        typesetAndScroll(bubble);
    }

    function setMessage(id, text) {
        var bubble = document.getElementById(id);
        if (!bubble) { return; }
        bubble.classList.remove('thinking');
        bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
        typesetAndScroll(bubble);
    }
    </script>
</body>
</html>
"""
_CHAT_HTML = _CHAT_HTML.replace("mathjax_src", _MATHJAX_SRC)



class ChatView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._pending_js = []
        self._id_counter = itertools.count(1)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.page().setBackgroundColor(Qt.transparent)
        self.setContextMenuPolicy(Qt.NoContextMenu)

        self.loadFinished.connect(self._on_load_finished)
        self.setHtml(_CHAT_HTML, QUrl("about:blank"))

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

    def __init__(self):
        super().__init__(get_translation("ui.sub.question"))
        self.add_widget(self._build_message_area(), stretch=1)
        self.add_widget(self._build_input_area())

        # 当前正在接收流式分片的消息 id / 累积文本（None 表示空闲）
        self._streaming_id = None
        self._streaming_text = ""

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(self._STREAM_THROTTLE_MS)
        self._render_timer.timeout.connect(self._flush_streaming)

    def _build_message_area(self) -> QWidget:
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet(
            "QFrame { background-color: #ffffff; border-radius: 10px; }"
        )
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_view = ChatView(card)
        card_layout.addWidget(self.chat_view)
        return card

    def _build_input_area(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText(
            get_translation("ui.sub.question.placeholder")
        )
        self.input_edit.returnPressed.connect(self._on_send)

        self.send_button = ui.PushButton(get_translation("ui.sub.question.send"))
        self.send_button.setFixedWidth(90)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self._on_send)

        row.addWidget(self.input_edit, stretch=1)
        row.addWidget(self.send_button)
        return container

    def recv_message(self, result):
        """流式分片回调：同一条 AI 回复的多个分片会被拼进同一个气泡里，
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

    def finish_recv(self):
        """AI 回复全部分片接收完毕。"""
        self._flush_streaming()
        self._streaming_id = None
        self._streaming_text = ""

    def _on_send(self):
        text = self.input_edit.text().strip()
        if not text:
            return
        t = defer.AICallBack(text, self)
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