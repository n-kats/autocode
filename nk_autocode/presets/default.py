import inspect
import os
from typing import Any

from dotenv import load_dotenv

from nk_autocode.framework import BaseAgent, Variable
from nk_autocode.presets.assistant import Assistant
from nk_autocode.presets.openai_agent import OpenAIAgent

_default_assistant = Assistant(
    verbose=False,
    interactive=False,
    regenerate=False,
    agent=OpenAIAgent(api_key=os.getenv("OPENAI_API_KEY")),
)


def autocode(
    description: str | None = None,
    args: list[str | Variable | dict] = None,
    kwargs: list[str | Variable | dict] = None,
    use_extra_args: bool = False,
    extra_args_type: type | None = None,
    use_extra_kwargs: bool = False,
    extra_kwargs_type: type | None = None,
    return_type: type | None = None,
    name: str = None,
    id: str | None = None,
    tools: list[Any] = None,
    refs: list[Any] = None,
    override: str | None = None,
    verbose: bool = None,
    interactive: bool = None,
    regenerate: bool = None,
    decorator: bool = False,
    agent: BaseAgent | None = None,
) -> Any:
    return _default_assistant.autocode(
        description=description,
        args=args,
        kwargs=kwargs,
        use_extra_args=use_extra_args,
        extra_args_type=extra_args_type,
        use_extra_kwargs=use_extra_kwargs,
        extra_kwargs_type=extra_kwargs_type,
        return_type=return_type,
        name=name,
        id=id,
        tools=tools,
        refs=refs,
        override=override,
        verbose=verbose,
        interactive=interactive,
        regenerate=regenerate,
        agent=agent,
        decorator=decorator,
        stack=inspect.stack()[1:],
    )


def setup_autocode(
    dotenv_path: str | None = None,
    verbose: bool = False,
    interactive: bool = False,
    regenerate: bool = False,
    agent: BaseAgent | None = None,
):
    global _default_assistant
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
    if agent is None:
        agent = OpenAIAgent(api_key=os.getenv("OPENAI_API_KEY"))
    _default_assistant = Assistant(
        verbose=verbose,
        interactive=interactive,
        regenerate=regenerate,
        agent=agent,
    )
