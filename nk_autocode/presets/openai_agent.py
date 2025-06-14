import re

import openai

from nk_autocode.framework import BaseAgent, Context, ErrorFeedback, HumanFeedback, Variable


def type_str_from_variable(var: Variable) -> str:
    if isinstance(var.type, type):
        return var.type.__name__
    else:
        return str(var.type)


class OpenAIAgent(BaseAgent):
    """OpenAI API を利用するエージェント実装"""

    def __init__(self, api_key: str, model: str = "gpt-4.1", temperature: float = 0):
        openai.api_key = api_key
        self.model = model
        self.temperature = temperature

    def generate_prompt(self, context: Context) -> str:
        prompt = ""
        if context.name:
            prompt += f"### Function Name\n{context.name}\n\n"
        if context.id:
            prompt += f"### ID: {context.id}\n\n"
        if context.description:
            prompt += f"### Function Description\n{context.description}\n\n"
        if context.docstring:
            prompt += f"### Docstring\n{context.docstring}\n\n"

        prompt += "### Parameters\n"
        if context.args is not None:
            if context.args:
                for var in context.args:
                    type_str = var.type if isinstance(var.type, str) else var.type.__name__ if var.type else "Any"
                    prompt += f"- {var.var}: {type_str}"
                    if var.default is not None:
                        prompt += f" = {var.default}"
                    prompt += "\n"
            else:
                prompt += "- No positional arguments\n"
        if context.use_extra_args:
            et = context.extra_args_type.__name__ if context.extra_args_type else "Any"
            prompt += f"- *args: {et}\n"

        if context.kwargs is not None:
            if context.kwargs:
                for var in context.kwargs:
                    prompt += f"- {var.var}: {type_str_from_variable(var)}"
                    if var.default is not None:
                        prompt += f" = {var.default}"
                    prompt += "\n"
            else:
                prompt += "- No keyword arguments\n"
        if context.use_extra_kwargs:
            kt = context.extra_kwargs_type.__name__ if context.extra_kwargs_type else "Any"
            prompt += f"- **kwargs: {kt}\n"
        if context.return_type:
            prompt += f"\n### Returns\n{context.return_type.__name__}\n"
        if context.feedbacks:
            prompt += "\n### Feedbacks\n"
            for fb in context.feedbacks:
                match fb:
                    case HumanFeedback(feedback=txt, previous_code=prev):
                        prompt += f"- Previous Code:\n{prev}\n"
                        prompt += f"- Human: {txt}\n"
                    case ErrorFeedback(error_message=err):
                        prompt += f"- Error: {err}\n"
        return prompt.strip()

    def generate_code(self, context: Context, verbose: bool = False) -> str:
        prompt = self.generate_prompt(context)
        if verbose:
            print(f"Generated Prompt:\n{prompt}\n")
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": get_prompt(),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
        )
        content = resp.choices[0].message.content
        m = re.search(r"```(?:python)?\n(.*?)(?:```|$)", content, re.S)
        return m.group(1).strip() if m else content.strip()


def get_prompt() -> str:
    """
    Returns:
        str: The instruction part of the prompt.
    """
    prompt = """Generate Python code that meets the following conditions:
- It should be written in Python.
- It should be executable.
- It should comply with PEP 8 standards.
- It should be compatible with Python 3.12.
- It should use new-style type hints as much as possible.
  - `list[str]` instead of `List[str]`. (also for dict, set, tuple, etc.)
  - `str | None` instead of `Optional[str]`.
- It should use type hints as much as possible.
- It should include a Google style docstring.
- It should be efficient and optimized.
- Comments in the code should be based on the provided description.
- Use long strings (\"\"\"...\"\"\") for multi-line string. but not for multi-line comments.
- This rule should be followed strictly. However, provided descriptions are more important than the rules.a
- Docstring should be detailed based on the provided description.
- Comments should mean why the code is not other way, not what the code does.
"""
    return prompt
