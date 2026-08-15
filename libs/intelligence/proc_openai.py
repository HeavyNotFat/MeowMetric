from openai import OpenAI

from .. import Config
from .. import encode_image
from .. import extract_json
from .. import get_prompt


client = OpenAI(
    api_key=Config.cloud_api_key,
    base_url=Config.cloud_api_base_url,
)


def cloud_ai_file_analysis_callback(filepath: str) -> dict | None:
    if not filepath.strip(): return {}
    base64_image = encode_image(filepath)
    completion = client.chat.completions.create(
        model=Config.cloud_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": f"data:image/png;base64,{base64_image}"},
                    {"type": "text", "text": get_prompt("file_analysis")},
                ],
            },
        ],
        extra_body={"enable_thinking": False},
    )
    answer = extract_json(completion.choices[0].message.content)
    return answer
