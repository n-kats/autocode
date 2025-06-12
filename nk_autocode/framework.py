from abc import ABC, abstractmethod
from typing import Any
import inspect

from pydantic import BaseModel, Field


class Variable(BaseModel):
    """関数の引数やキーワード引数を表す"""

    var: str
    type: Any | None = Any
    default: Any | None = None


class HumanFeedback(BaseModel):
    """人間が入力するコードに関するフィードバック"""

    previous_code: str
    feedback: str


class ErrorFeedback(BaseModel):
    """コード実行時のエラー情報フィードバック"""
    previous_code: str
    error_message: str


Feedback = HumanFeedback | ErrorFeedback


class Context(BaseModel):
    """コード生成 に渡すコンテキスト情報"""

    description: str | None = Field(
        default=None,
        description="Function description for code generation")
    docstring: str | None = None
    args: list[Variable]
    kwargs: list[Variable]
    use_extra_args: bool
    extra_args_type: type | None
    use_extra_kwargs: bool
    extra_kwargs_type: type | None
    return_type: type | None
    name: str | None
    id: str | None
    tools: list[Any]
    refs: list[Any]
    feedbacks: list[Feedback] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
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
        feedbacks: list[Feedback] | None = None,
        stack: list[inspect.FrameInfo] | None = None,
    ) -> "Context":
        def to_vars(raw: list[str | Variable | dict] | None) -> list[Variable]:
            items: list[Variable] = []
            for item in raw or []:
                match item:
                    case Variable():
                        items.append(item)
                    case str():
                        items.append(Variable(var=item))
                    case dict():
                        items.append(Variable(**item))
                    case _:
                        raise TypeError(f"Invalid arg type: {type(item)}")
            return items
        return cls(
            description=description,
            args=to_vars(args),
            kwargs=to_vars(kwargs),
            use_extra_args=use_extra_args,
            extra_args_type=extra_args_type,
            use_extra_kwargs=use_extra_kwargs,
            extra_kwargs_type=extra_kwargs_type,
            return_type=return_type,
            name=name,
            id=id,
            tools=tools or [],
            refs=refs or [],
            feedbacks=feedbacks or [],
            stack=stack,
        )


class BaseAgent(ABC):
    """コード生成のためのエージェントインターフェース"""

    @abstractmethod
    def generate_code(self, context: Context, verbose: bool = False) -> str:
        """コンテキストをもとにコード生成し、Python のコード文字列を返す"""
        raise NotImplementedError


class BaseAssistant(ABC):
    """コード生成を行うアシスタント"""

    @abstractmethod
    def autocode(
        self,
        description: str | None,
        args: list[str | Variable | dict],
        kwargs: list[str | Variable | dict],
        use_extra_args: bool,
        extra_args_type: type | None,
        use_extra_kwargs: bool,
        extra_kwargs_type: type | None,
        return_type: type | None,
        name: str | None,
        id: str | None,
        tools: list[Any],
        refs: list[Any],
        override: str | None,
        verbose: bool,
        interactive: bool,
        regenerate: bool,
        agent: BaseAgent | None,
        stack: list[inspect.FrameInfo] | None = None,
        decorator: bool = False,
    ) -> Any:
        """コンテキストをもとにコード生成を行う"""


class GiveUpGenerationError(Exception):
    """コード生成をあきらめたことを示す例外"""
