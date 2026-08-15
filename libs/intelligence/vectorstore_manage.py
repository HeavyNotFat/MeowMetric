import os
import json
import shutil
import logging
from typing import Optional, Dict, Any

from langchain_chroma import Chroma
from .. import Config
from . import rag

logger = logging.getLogger(__name__)

CHROMA_BASE_DIR = './resources/chroma_rag'
VERSION_FILE = os.path.join(CHROMA_BASE_DIR, 'version.json')
DOCS_FOLDER = './resources/rag/'


def _get_version_info() -> Dict[str, Any]:
    """读取当前生效的版本信息"""
    if not os.path.exists(VERSION_FILE):
        return {"current": None, "model": None, "dimension": None}
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_version_info(info: Dict[str, Any]):
    """原子写入版本信息（先写临时文件再重命名）"""
    tmp_file = VERSION_FILE + '.tmp'
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, VERSION_FILE)  # 原子操作


def get_or_create_vectorstore(embeddings, force_rebuild: bool = False) -> Chroma:
    """
    智能获取 VectorStore：
      若模型/维度匹配且无需强制重建 → 直接加载现有 Collection
      否则 → 创建新 Collection，构建索引，原子切换版本
    """
    os.makedirs(CHROMA_BASE_DIR, exist_ok=True)

    current_model = Config.embed_model
    # 获取当前 embedding 维度（取一个样本探测）
    sample_dim = len(embeddings.embed_query("dimension_probe"))

    version_info = _get_version_info()
    current_collection = version_info.get("current")

    # 版本匹配，直接复用
    if (not force_rebuild
            and current_collection
            and version_info.get("model") == current_model
            and version_info.get("dimension") == sample_dim):

        collection_path = os.path.join(CHROMA_BASE_DIR, current_collection)
        if os.path.exists(collection_path):
            logger.info(f"✅ 复用现有向量库: {current_collection} (dim={sample_dim})")
            return Chroma(
                persist_directory=collection_path,
                embedding_function=embeddings,
                collection_name=current_collection
            )

    # 需要新建/重建
    new_collection_name = f"rag_v_{int(__import__('time').time())}"
    new_collection_path = os.path.join(CHROMA_BASE_DIR, new_collection_name)

    logger.info(f"🔨 构建新向量库: {new_collection_name} (model={current_model}, dim={sample_dim})")

    raw_docs = rag.load_documents(DOCS_FOLDER)
    splits = rag.split_math_documents(raw_docs, max_length=1800)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=new_collection_path,
        collection_name=new_collection_name
    )

    # 切换版本
    old_collection = current_collection
    _save_version_info({
        "current": new_collection_name,
        "model": current_model,
        "dimension": sample_dim,
        "doc_count": len(splits)
    })
    logger.info(f"✅ 版本已切换: {old_collection} → {new_collection_name}")

    if old_collection and old_collection != new_collection_name:
        old_path = os.path.join(CHROMA_BASE_DIR, old_collection)
        if os.path.exists(old_path):
            try:
                shutil.rmtree(old_path)
                logger.info(f"🗑️ 已清理旧版本: {old_collection}")
            except Exception as e:
                logger.warning(f"⚠️ 清理旧版本失败: {e}")

    return vectorstore
