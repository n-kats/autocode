from typing import Any, Type

from pydantic import BaseModel

from nk_autodoc.framework import LanguageModel


class AutoType(BaseModel):
    code: str
    class_name: str

    def to_model(self) -> Type[BaseModel]:
        ns: dict[str, Any] = {}
        exec(self.code, ns)
        return ns[self.class_name]  # type: ignore


auto_type_cache: dict[str, AutoType] = {}


def auto_type(
    model: LanguageModel, type_description: str, cache: dict[str, AutoType] = auto_type_cache
) -> Type[BaseModel]:
    if type_description in cache:
        return cache[type_description].to_model()
    prompt = f"""以下のデータ構造を持つデータの形式を表すpydanticモデルのコードを生成してください。
{type_description}

# ルール
- コードはPythonのpydanticライブラリを使用して記述してください。
- Anyのような曖昧な型は使用しないでください。推測ができない場合はstr型を使用してください。
"""
    response = model(prompt, output_structure=AutoType)
    cache[type_description] = response
    return response.to_model()  # type: ignore
