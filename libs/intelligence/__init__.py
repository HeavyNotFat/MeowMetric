import os
from typing import Iterator

from .. import get_prompt
from . import rag

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

DOCS_FOLDER = "./resources/rag/"
CHROMA_DIR = "./resources/chroma_r1_db"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "deepseek-r1:7b"


def ai_callback(query: str) -> Iterator[dict]:
    """
    生成器版本：每次 yield 一个事件字典
    事件类型: status(初始化进度) / content(正文流式内容) / done(结束) / error
    :param query: 用户输入的问题
    """
    try:
        yield {"type": "status", "data": "开始初始化"}

        embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        if os.path.exists(CHROMA_DIR):
            vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        else:
            raw_docs = rag.load_documents(DOCS_FOLDER)
            splits = rag.split_math_documents(raw_docs, max_length=1800)

            yield {"type": "status", "data": f"共切分为 {len(splits)} 个数学题块"}
            vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory=CHROMA_DIR
            )
        yield {"type": "status", "data": "已创建向量仓库"}

        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        prompt = ChatPromptTemplate.from_template(get_prompt("math"))
        llm = ChatOllama(
            model=CHAT_MODEL,
            num_ctx=8192,
            temperature=0,
            num_predict=2048
        )
        rag_chain_stream = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
        )

        yield {"type": "status", "data": "初始化完成"}

        buffer = ""
        in_think = False

        for chunk in rag_chain_stream.stream(query):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            buffer += text

            while True:
                if not in_think:
                    start = buffer.find("<think>")
                    if start == -1:
                        if buffer:
                            yield {"type": "content", "data": buffer}
                        buffer = ""
                        break
                    else:
                        if buffer[:start]:
                            yield {"type": "content", "data": buffer[:start]}
                        buffer = buffer[start + len("<think>"):]
                        in_think = True
                else:
                    end = buffer.find("</think>")
                    if end == -1:
                        buffer = ""
                        break
                    else:
                        buffer = buffer[end + len("</think>"):]
                        in_think = False

        if buffer and not in_think:
            yield {"type": "content", "data": buffer}

        yield {"type": "done", "data": None}

    except Exception as e:
        yield {"type": "error", "data": str(e)}
