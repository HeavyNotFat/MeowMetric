from enum import Enum
import json
import re
import base64
from dataclasses import dataclass, fields

import polib

CONFIG_PATH = "./resources/config.json"


class Languages(Enum):
    Chinese = "zh-cn"


@dataclass
class _BaseModelConfig:
    language: str = Languages.Chinese.value
    cloud_api_base_url: str = ""
    cloud_api_key: str = ""
    cloud_model: str = ""
    embed_model: str = ""
    model_request: str = ""

    def __setitem__(self, key, value):
        setattr(self, key, value)


class DataMemShared:
    embedding_models: list = []
    generative_models: list = []


class ConfigLoader:
    @staticmethod
    def load_config() -> _BaseModelConfig:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            f.close()

        valid_keys = {field.name for field in fields(_BaseModelConfig)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}

        return _BaseModelConfig(**filtered)


    @staticmethod
    def save_config(config: _BaseModelConfig) -> None:
        config = {field.name: getattr(config, field.name) for field in fields(config)}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        data = base64.b64encode(image_file.read()).decode("utf-8")
        f.close()
    return data


def extract_json(answer: str) -> dict | list:
    """从AI回答中提取JSON部分，忽略前后的多余文本。"""
    if not answer or not isinstance(answer, str):
        return {}

    # 先尝试直接解析
    try:
        return json.loads(answer)
    except (json.JSONDecodeError, ValueError):
        pass

    # 尝试提取 ```json ... ``` 代码块
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", answer, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # 尝试找到第一个 { 或 [ 到最后一个 } 或 ] 之间的内容
    brace_start = answer.find("{")
    bracket_start = answer.find("[")

    # 确定起始位置
    if brace_start == -1 and bracket_start == -1:
        return {}
    elif brace_start == -1:
        start = bracket_start
        end_char = "]"
    elif bracket_start == -1:
        start = brace_start
        end_char = "}"
    else:
        start = min(brace_start, bracket_start)
        end_char = "}" if brace_start <= bracket_start else "]"

    # 从末尾向前找对应的结束符
    end = answer.rfind(end_char)
    if end != -1 and end > start:
        candidate = answer[start : end + 1]
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass

    return {}


def get_translation(key: str) -> str:
    mo = polib.mofile(f"./resources/languages/{Config.language}.mo")
    translation = mo.find(key)
    return translation.msgstr


def get_prompt(key: str) -> str:
    return prompts[key]


Config = ConfigLoader.load_config()
with open(f"./resources/prompts/prompts-{Config.language}.json", 'r', encoding='utf-8') as f:
    prompts = json.load(f)
    f.close()
