import os
import re
from typing import List

from langchain_community.document_loaders import TextLoader, Docx2txtLoader
from langchain_core.documents import Document


def load_documents(folder_path: str) -> List[Document]:
    """
    加载文件夹中的所有 .txt 或 .docx 文件
    :param folder_path:  文件夹路径
    :return: 文档列表
    """
    docs = []

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)

        if not os.path.isfile(filepath):
            continue

        try:
            if filename.endswith(".txt"):
                loader = TextLoader(filepath, encoding="utf-8")
            elif filename.endswith((".docx", ".doc")):
                loader = Docx2txtLoader(filepath)
            else:
                continue

            loaded = loader.load()

            for doc in loaded:
                doc.metadata["source"] = filename

            docs.extend(loaded)
            print(f"✅ 成功加载: {filename}")

        except Exception as e:
            print(f"❌ 加载失败 {filename}: {e}")

    if not docs:
        raise ValueError(f"在 {folder_path} 中未找到任何 .txt 或 .docx 文件")

    return docs


def split_math_documents(docs: List[Document], max_length: int = 1800) -> List[Document]:
    """
    按 \\item 切分数学题，每道题一个 chunk；
    超长题再按 （1）（2）（i）（ii） 细分。
    :param docs: 文档列表
    :param max_length: 最长长度
    :return: 切分后的LaTex
    """
    result = []

    for doc in docs:
        text = doc.page_content

        # 按 \\item 切分
        questions = re.split(r"(?=\\\\item\\s)", text)
        for q in questions:
            q = q.strip()
            if len(q) < 20:
                continue

            # 长题再细分
            if len(q) > max_length:
                subs = re.split(r"(?=（[0-9ivIV]+）)", q)
                for s in subs:
                    s = s.strip()
                    if len(s) < 20:
                        continue

                    result.append(
                        Document(
                            page_content=s,
                            metadata=doc.metadata.copy()
                        )
                    )
            else:
                result.append(
                    Document(
                        page_content=q,
                        metadata=doc.metadata.copy()
                    )
                )

    return result
