from typing import Any

from nk_autodoc.framework import BaseCompressor, BaseOutput, BaseWriter, Context, LanguageModel
from nk_autodoc.utils.auto_type import auto_type


class Writer(BaseWriter):
    def __init__(self, model: LanguageModel, context: Context, output: BaseOutput):
        self.model = model
        self.context = context
        self.output = output

    def sub_writer(self, context: Context) -> "Writer":
        return Writer(self.model, context.copy(), output=self.output)

    def add_context(self, context: Context, compressor: BaseCompressor) -> None:
        compressed_context = compressor(context)
        self.context.merge(compressed_context)

    def compress(self, compressor: BaseCompressor) -> None:
        compressed_context = compressor(self.context)
        self.context = compressed_context

    def __call__(self, text: str) -> None:
        generated_text = self._generate_text(text)
        self.context.add(generated_text)
        self.output.print(generated_text)

    def _generate_text(self, text: str) -> str:
        return self.model(self._generation_prompt(text))  # type: ignore

    def _generation_prompt(self, text: str) -> str:
        lines = []
        lines.append("あなたの役割は、文章の中に以下の項目についての部分の文章を作成することです。")
        lines.append("# 生成すべき項目")
        lines.append(text)

        if self.context.entities:
            lines.append("# 既存の情報")
            for entity in self.context.entities:
                if entity.text:
                    lines.append(entity.text)
                    lines.append("")

            lines.append("# 生成すべき項目（再掲）")
            lines.append(text)

        lines.append("")
        lines.append("# 出力ルール")
        lines.append("- 出力は日本語で行うこと")
        lines.append("- 出力は目的の文章のみを返すこと")
        lines.append("- 生成すべき項目で「〇〇を書く」と有る場合、〇〇のパートの文章を出力することを意味します。")
        lines.append("- 文字数・分量の指定がある場合は、指定された文字数・分量に従うこと")

        return "\n".join(lines)

    def plan(self, text: str, type_auto: str | None = None) -> Any:
        prompt = self._plan_prompt(text)
        if type_auto:
            output_structure = auto_type(self.model, type_auto)
        else:
            output_structure = None
        response = self.model(prompt, output_structure=output_structure)
        if isinstance(response, str):
            self.context.add(response)
        else:
            self.context.add(str(response.model_dump()))
        return response

    def _plan_prompt(self, text: str) -> str:
        lines = []
        lines.append("あなたの役割は、以下の項目についての計画を立てることです。")
        lines.append("# 計画を立てる項目")
        lines.append(text)

        if self.context.entities:
            lines.append("# 既存のコンテキスト・計画")
            for entity in self.context.entities:
                if entity.text:
                    lines.append(entity.text)
                    lines.append("")

            lines.append("# 計画を立てる項目（再掲）")
            lines.append(text)
            lines.append("")

        lines.append("# 出力ルール")
        lines.append("- 出力は日本語で行うこと")
        lines.append("- 出力は計画の内容のみを返すこと")
        lines.append("- 具体的に決めるべきところは具体的に決めること")
        lines.append("- 文字数・分量の指定がある場合は、指定された文字数・分量を十二分に考慮した計画を立てること")

        return "\n".join(lines)
