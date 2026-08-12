import os.path
from enum import Enum
import json

import polib

with open("./resources/prompts/prompts.json" if os.path.exists("./resources/prompts/prompts.json")
          else "../resources/prompts/prompts.json", 'r', encoding='utf-8') as f:
    prompts = json.load(f)
    f.close()


class Languages(Enum):
    Chinese = "zh-cn"


class DataMemSharing:
    language: str = Languages.Chinese.value


def get_translation(key: str) -> str:
    mo = polib.pofile(f"./resources/languages/{DataMemSharing.language}.po")
    translation = mo.find(key)
    return translation.msgstr


def get_prompt(key: str) -> str:
    return prompts[key]

