import sys
import os
import json

from flask import Flask, request, Response, stream_with_context

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_dir)

from libs import intelligence

app = Flask(__name__)


def sse_format(event: dict) -> str:
    """把事件字典包装成 SSE 格式的一行"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.route('/api/ai/stream', methods=['POST'])
def ai_callback_stream():
    """
    流式接口：SSE (Server-Sent Events)
    """
    payload = request.get_json(silent=True) or {}
    query = payload.get("query", "")

    def generate():
        try:
            for event in intelligence.ai_callback(query=query):
                yield sse_format(event)
        except Exception as e:
            yield sse_format({"type": "error", "data": str(e)})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


def run(host, port=5000, debug=False, threaded=True):
    app.run(host=host, port=port, debug=debug, threaded=threaded)


if __name__ == '__main__':
    run('0.0.0.0')
