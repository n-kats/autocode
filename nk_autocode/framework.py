import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable

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

    description: str | None = Field(default=None, description="Function description for code generation")
    docstring: str | None = None
    args: list[Variable] | None
    kwargs: list[Variable] | None
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
    stack: list[inspect.FrameInfo] | None = None

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
        name: str | None = None,
        description: str | None = None,
        id: str | None = None,
        args: list[str | Variable | dict] | None = None,
        kwargs: list[str | Variable | dict] | None = None,
        use_extra_args: bool = False,
        extra_args_type: type | None = None,
        use_extra_kwargs: bool = False,
        extra_kwargs_type: type | None = None,
        return_type: type | None = None,
        tools: list[Any] | None = None,
        refs: list[Any] | None = None,
        override: str | None = None,
        agent: BaseAgent | None = None,
        regenerate: bool | None = None,
        stack: list[inspect.FrameInfo] | None = None,
        verbose: bool | None = None,
        interactive: bool | None = None,
        decorator: bool = False,
        dry_run: bool | None = None,
        dry_run_fn: Callable[..., Any] | None = None,
    ) -> "BaseGeneratedCode":
        """コンテキストをもとにコード生成を行う"""


class BaseGeneratedCode(ABC):
    """生成されたコードの抽象インターフェース"""

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """対象の関数を呼び出す"""


class CompiledCode(BaseGeneratedCode):
    """AI生成・コンパイル済みのコード"""

    def __init__(self, func: Callable[..., Any], source_code: str, context: Context) -> None:
        self.__func = func
        self.__source_code = source_code
        self.__context = context

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__func(*args, **kwargs)

    @property
    def source_code(self) -> str:
        """生成されたソースコード"""
        return self.__source_code

    @property
    def context(self) -> Context:
        """生成時のコンテキスト"""
        return self.__context


class CachedCode(BaseGeneratedCode):
    """キャッシュから読み込まれたコード"""

    def __init__(self, func: Callable[..., Any], cache_path: str) -> None:
        self.__func = func
        self.__cache_path = cache_path

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__func(*args, **kwargs)

    @property
    def cache_path(self) -> str:
        """キャッシュファイルのパス"""
        return self.__cache_path


class ImportedCode(BaseGeneratedCode):
    """外部ファイルからインポートされたコード"""

    def __init__(self, func: Callable[..., Any], module_name: str, file_path: str) -> None:
        self.__func = func
        self.__module_name = module_name
        self.__file_path = file_path

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__func(*args, **kwargs)

    @property
    def module_name(self) -> str:
        """モジュール名"""
        return self.__module_name

    @property
    def file_path(self) -> str:
        """ファイルパス"""
        return self.__file_path


class DryRunCode(BaseGeneratedCode):
    """ドライラン用のコード"""

    def __init__(self, dry_run_fn: Callable[..., Any], description: str | None = None) -> None:
        self.__dry_run_fn = dry_run_fn
        self.__description = description

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__dry_run_fn(*args, **kwargs)

    @property
    def description(self) -> str | None:
        """関数の説明"""
        return self.__description


class DecoratorCode(BaseGeneratedCode):
    """デコレータで定義されたコード"""

    def __init__(self, func: Callable[..., Any], function_name: str) -> None:
        self.__func = func
        self.__function_name = function_name

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__func(*args, **kwargs)

    @property
    def function_name(self) -> str:
        """デコレータで定義された関数名"""
        return self.__function_name


class GiveUpGenerationError(Exception):
    """コード生成をあきらめたことを示す例外"""
