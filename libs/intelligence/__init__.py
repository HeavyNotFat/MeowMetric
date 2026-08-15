from functools import lru_cache
from typing import Iterator, List, Optional

from .. import encode_image
from .. import get_prompt


def get_embeddings():
    from .. import Config
    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=Config.embed_model)


def get_vectorstore():
    from . import vectorstore_manage

    embeddings = get_embeddings()
    return vectorstore_manage.get_or_create_vectorstore(embeddings)


@lru_cache(maxsize=1)
def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": 4})


@lru_cache(maxsize=1)
def get_prompt_template():
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_template(get_prompt('general'))


def get_llm(model: str):
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model,
        num_ctx=20480,
        temperature=0,
        num_predict=-1,
    )


def _build_text_messages(query: str, context: str) -> list:
    """构建纯文本消息列表"""
    prompt_template = get_prompt_template()
    system_content = prompt_template.format(context=context, question=query)
    return [
        {"role": "system", "content": system_content},
        {"role": "user",   "content": query},
    ]


def _build_multimodal_messages(query: str, context: str, image_paths: List[str]) -> list:
    """构建含图片的多模态消息列表"""
    prompt_template = get_prompt_template()
    system_content = prompt_template.format(context=context, question=query)

    user_content: list = [{"type": "text", "text": query}]
    for path in image_paths:
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"}})

    return [
        {"role": "system", "content": system_content},
        {"role": "user",   "content": user_content},
    ]


def _retrieve_context(query: str) -> str:
    """检索 RAG 上下文，失败时返回空字符串"""
    try:
        docs = get_retriever().invoke(query)
        return "\n\n".join(doc.page_content for doc in docs)
    except Exception:
        return ""


def _stream_with_think_parser(llm_stream) -> Iterator[dict]:
    """
    通用流式解析器：处理 <think>...</think> 标签 + 正常内容
    接收任意可迭代的 chunk 流，yield 标准化事件字典
    """
    in_think = False
    buffer = ""

    for chunk in llm_stream:
        text = getattr(chunk, "content", "") or str(chunk)
        buffer += text

        while True:
            if not in_think:
                pos = buffer.find("<think>")
                if pos == -1:
                    if buffer:
                        yield {"type": "content", "data": buffer}
                    buffer = ""
                    break
                # 找到 <think>
                if pos > 0:
                    yield {"type": "content", "data": buffer[:pos]}
                buffer = buffer[pos + len("<think>"):]
                in_think = True
            else:
                end = buffer.find("</think>")
                if end == -1:
                    break  # 等待更多数据
                # 跳过 </think> 及其之前的内容
                buffer = buffer[end + len("</think>"):]
                in_think = False

    # 流结束后残留的非 think 内容
    if buffer and not in_think:
        yield {"type": "content", "data": buffer}


def local_ai_callback(
    query: str,
    model: str,
    images: Optional[List[str]] = None,
) -> Iterator[dict]:
    """
    统一 AI 回调入口

    :param query:  用户问题
    :param model:  Ollama 模型名
    :param images: 可选图片路径列表；为 None 或空时走纯文本模式
    """
    try:
        yield {"type": "status", "data": "初始化中..."}

        context = _retrieve_context(query)

        has_images = bool(images)
        if has_images:
            messages = _build_multimodal_messages(get_prompt("file_analysis"), context, images)
        else:
            messages = _build_text_messages(query, context)

        yield {"type": "status", "data": "开始生成回答"}

        llm = get_llm(model)
        stream = llm.stream(messages)

        for event in _stream_with_think_parser(stream):
            yield event

        yield {"type": "done", "data": None}

    except Exception as e:
        yield {"type": "error", "data": str(e)}
