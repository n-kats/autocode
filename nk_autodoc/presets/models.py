import base64
import os
from io import BytesIO
from typing import Any, Type

import openai
from PIL import Image
from pydantic import BaseModel

from nk_autodoc.framework import LanguageModel


class OpenAIModel(LanguageModel):
    def __init__(self, model: str = "gpt-4.1", api_key_key: str | None = None):
        self.model = model
        self.client = openai.OpenAI(api_key=os.getenv(api_key_key) if api_key_key else None)

    def __call__(self, prompt: str | list[str | Image.Image], output_structure: Type[BaseModel] | None = None) -> Any:
        contents = []
        if isinstance(prompt, str):
            contents.append({"type": "input_text", "text": prompt})
        elif isinstance(prompt, list):
            for item in prompt:
                if isinstance(item, str):
                    contents.append({"type": "input_text", "text": item})
                elif isinstance(item, Image.Image):
                    contents.append(to_image_content(item, "png"))
                else:
                    raise ValueError("Unsupported prompt type: {}".format(type(item)))

        if output_structure is not None:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": contents,  # type: ignore
                    }
                ],
                text_format=output_structure,
            )
            return response.output_parsed
        else:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": contents,  # type: ignore
                    }
                ],
            )
            return response.output_text


def to_image_content(image: Image.Image, image_type: str) -> dict[str, str]:
    with BytesIO() as f_out:
        image.save(f_out, format=image_type)
        encoded = base64.b64encode(f_out.getvalue()).decode("utf-8")
    return {
        "type": "input_image",
        "image_url": f"data:image/{image_type};base64,{encoded}",
    }
