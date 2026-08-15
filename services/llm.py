import sys
import os
import json
import subprocess
import requests

from flask import Flask, request, Response, stream_with_context
from waitress import serve

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_dir)

app = Flask(__name__)
EMBEDDING_MODELS = [
    "nomic-embed-text",
    "bge-m3",
    "qwen3-embedding"
]


def sse_format(event: dict) -> str:
    """把事件字典包装成 SSE 格式的一行"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def is_embedding_model(model_name: str):
    """
    通过调用 /api/embeddings 接口判断模型是否为嵌入模型
    返回 True 表示是嵌入模型，False 表示不是或调用失败
    """
    try:
        resp = requests.post(
            f"http://localhost:11434/api/embeddings",
            json={"model": model_name, "prompt": "test"},
            timeout=10
        )
        if resp.status_code != 200:
            return False

        data = resp.json()
        return (
            "embedding" in data
            and isinstance(data["embedding"], list)
            and len(data["embedding"]) > 0
        )
    except Exception:
        return False


@app.route('/api/ai/local', methods=['POST'])
def local_ai_callback_stream():
    """
    流式接口：SSE (Server-Sent Events)
    """
    from libs import intelligence

    payload = request.get_json(silent=True) or {}

    query = payload.get("query", "")
    model = payload.get("model", "")

    filepath = payload.get("filepath", None)
    if isinstance(filepath, str): filepath = [filepath]

    def generate():
        try:
            for event in intelligence.local_ai_callback(query=query, model=model, images=filepath):
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


@app.route('/api/ai/cloud', methods=['POST'])
def cloud_ai_callback():
    from libs.intelligence import proc_openai

    payload = request.get_json(silent=True) or {}
    filepath = payload.get("filepath", "")
    if not filepath: return {}

    return proc_openai.cloud_ai_file_analysis_callback(filepath)


@app.route('/api/get_model_lists', methods=['POST'])
def get_model_lists():
    """
    流式获取本地 Ollama 已安装模型 (SSE)
    每检测完一个模型就立即推送给前端
    """
    def generate():
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10
            )

            if result.returncode != 0:
                yield sse_format({"type": "error", "data": "Failed to run ollama list"})
                return

            lines = result.stdout.strip().splitlines()

            model_lines = [l for l in lines[1:] if l.split()]

            for idx, line in enumerate(model_lines, 1):
                parts = line.split()
                if not parts:
                    continue

                model_name = parts[0]
                model_type = "generative"

                if "embed" in model_name.lower() or model_name in EMBEDDING_MODELS:
                    model_type = "embedding"
                else:
                    if is_embedding_model(model_name):
                        model_type = "embedding"
                yield sse_format({
                    "type": "model",
                    "data": {
                        "name": model_name,
                        "category": model_type,
                        "index": idx,
                        "total": len(model_lines)
                    }
                })

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


def run(host, port=5000, threads: int = 4):
    serve(app, host=host, port=port, threads=threads)


if __name__ == '__main__':
    run('0.0.0.0')
