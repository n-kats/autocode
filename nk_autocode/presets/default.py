import inspect
import os
from typing import Any, Callable

from dotenv import load_dotenv

from nk_autocode.editor import Editor
from nk_autocode.framework import BaseAgent, BaseGeneratedCode, Variable
from nk_autocode.presets.assistant import Assistant
from nk_autocode.presets.openai_agent import OpenAIAgent

_default_assistant: Assistant


def autocode(
    description: str | None = None,
    args: list[str | Variable | dict] | None = None,
    kwargs: list[str | Variable | dict] | None = None,
    use_extra_args: bool = False,
    extra_args_type: type | None = None,
    use_extra_kwargs: bool = False,
    extra_kwargs_type: type | None = None,
    return_type: type | None = None,
    name: str | None = None,
    id: str | None = None,
    tools: list[Any] | None = None,
    refs: list[Any] | None = None,
    override: str | None = None,
    verbose: bool | None = None,
    interactive: bool | None = None,
    regenerate: bool | None = None,
    decorator: bool = False,
    agent: BaseAgent | None = None,
    dry_run: bool | None = None,
    dry_run_fn: Callable | None = None,
) -> BaseGeneratedCode:
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
        dry_run=dry_run,
        dry_run_fn=dry_run_fn,
    )


def setup_autocode(
    dotenv_path: str | None = None,
    verbose: bool = False,
    interactive: bool = False,
    regenerate: bool = False,
    agent: BaseAgent | None = None,
    editor: Editor | None = None,
    dry_run: bool | None = None,
    dry_run_fn: Callable | None = None,
) -> None:
    global _default_assistant
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)

    if agent is None:
        agent = OpenAIAgent(api_key=os.getenv("OPENAI_API_KEY"))

    if editor is None:
        editor_in_env = os.getenv("EDITOR")
        if editor_in_env:
            editor = Editor(editor_in_env)

    _default_assistant = Assistant(
        verbose=verbose,
        interactive=interactive,
        regenerate=regenerate,
        agent=agent,
        dry_run=dry_run,
        dry_run_fn=dry_run_fn,
        editor=editor,
    )


setup_autocode()


def return_value(value: Any, verbose: bool = False) -> Callable[..., Any]:
    """
    Returns a function that prints the arguments and return value if verbose is True.
    This function is useful for dry_run_fn in autocode.
    Args:
        value: The value to return.
        verbose: If True, prints the arguments and return value.
    Returns:
        A function that takes any arguments and keyword arguments, and returns the value.
    Example:
        >>> fn = autocode(dry_run=True, dry_run_fn=return_value(42, verbose=True))
        >>> result = fn(1, 2, key="value")
        Arguments: (1, 2)
        Keyword Arguments: {'key': 'value'}
        Return Value: 42
        42
    """

    def fn(*args: Any, **kwargs: Any) -> Any:
        if verbose:
            print(f"Arguments: {args}")
            print(f"Keyword Arguments: {kwargs}")
            print(f"Return Value: {value}")

        return value

    return fn


def print_and_exception(*args: Any, **kwargs: Any) -> None:
    """
    Prints the arguments and raises an exception.
    Args:
        *args: Positional arguments to print.
        **kwargs: Keyword arguments to print.
    Raises:
        Exc    Exception: Always raises an exception after printing the arguments.
    Example:
        >>> autocode(dry_run=True, dry_run_fn=print_and_exception)
        Arguments: (1, 2)
        Keyword Arguments: {'key': 'value'}
        Exception: print_and_exception called, raising an exception.
    """
    print(f"Arguments: {args}")
    print(f"Keyword Arguments: {kwargs}")
    raise Exception("print_and_exception called, raising an exception.")
