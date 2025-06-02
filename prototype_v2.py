import inspect
import os
import re
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
import openai
from pydantic import BaseModel, Field


class HumanFeedback(BaseModel):
    """人間が入力するコードに関するフィードバック"""
    previous_code: str
    feedback: str


class ErrorFeedback(BaseModel):
    """コード実行時のエラー情報フィードバック"""
    error_message: str


Feedback = HumanFeedback | ErrorFeedback


class Variable(BaseModel):
    """関数の引数やキーワード引数を表す"""
    var: str
    type: Any | None = None
    default: Any | None = None


class Context(BaseModel):
    """コード生成 に渡すコンテキスト情報"""
    description: str = Field(
        description="Function description for code generation")
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
        description: str = "",
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
        )


class BaseAgent:
    """コード生成のためのエージェントインターフェース"""

    def generate_code(self, context: Context) -> str:
        """コンテキストをもとにコード生成し、Python のコード文字列を返す"""
        raise NotImplementedError


class OpenAIAgent(BaseAgent):
    """OpenAI API を利用するエージェント実装"""

    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0):
        openai.api_key = api_key
        self.model = model
        self.temperature = temperature

    def generate_prompt(self, context: Context) -> str:
        prompt = ""
        if context.name:
            prompt += f"### Function Name\n{context.name}\n\n"
        if context.id:
            prompt += f"### ID: {context.id}\n\n"
        prompt += f"### Function Description\n{context.description}\n\n"
        prompt += "### Parameters\n"
        for var in context.args:
            prompt += f"- {var.var}: {var.type.__name__ if var.type else 'Any'}"
            if var.default is not None:
                prompt += f" = {var.default}"
            prompt += "\n"
        if context.use_extra_args:
            et = context.extra_args_type.__name__ if context.extra_args_type else "Any"
            prompt += f"- *args: {et}\n"
        for var in context.kwargs:
            prompt += f"- {var.var}: {var.type.__name__ if var.type else 'Any'}"
            if var.default is not None:
                prompt += f" = {var.default}"
            prompt += "\n"
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

    def generate_code(self, context: Context) -> str:
        prompt = self.generate_prompt(context)
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant that can reason in multiple steps. You generate Python code based on the provided context. only return the code in a code block."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
        )
        content = resp.choices[0].message.content
        m = re.search(r"```(?:python)?\n(.*?)(?:```|$)", content, re.S)
        return m.group(1).strip() if m else content.strip()


class Assistant:
    def __init__(self, verbose: bool, interactive: bool, retry: bool, agent: BaseAgent):
        self.verbose = verbose
        self.interactive = interactive
        self.retry = retry
        self.agent = agent
        self._cache_root = Path("_cache/autocode")
        self._ids_dir = self._cache_root / "ids"
        self._structure_dir = self._cache_root / "structure"
        self._ids_dir.mkdir(parents=True, exist_ok=True)
        self._structure_dir.mkdir(parents=True, exist_ok=True)

    def autocode(
        self,
        description: str,
        args: list[str | Variable | dict],
        kwargs: list[str | Variable | dict],
        use_extra_args: bool,
        extra_args_type: type | None,
        use_extra_kwargs: bool,
        extra_kwargs_type: type | None,
        return_type: type | None,
        name: str,
        id: str | None,
        tools: list[Any],
        refs: list[Any],
        override: str | None,
        verbose: bool,
        interactive: bool,
        retry: bool,
        agent: BaseAgent | None,
    ) -> Any:
        if override:
            try:
                mod, fn = override.rsplit(":", 1)
                module = __import__(mod, fromlist=[fn])
                return getattr(module, fn)
            except (ImportError, AttributeError):
                pass
        ctx = Context.create(
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
        )
        _agent = agent or self.agent
        cache_path: Path | None = None
        if ctx.id:
            id_file = self._ids_dir / f"{ctx.id}.py"
            if id_file.is_file():
                cache_path = id_file
        if not cache_path:
            frame = inspect.stack()[2]
            caller_path = Path(frame.filename).relative_to(Path.cwd())
            struct_dir = self._structure_dir / caller_path.parent
            struct_dir.mkdir(parents=True, exist_ok=True)
            struct_file = struct_dir / f"{ctx.name}.py"
            if struct_file.is_file():
                cache_path = struct_file
        if cache_path:
            if verbose:
                print(f"[autocode] Loaded code from cache: {cache_path}")
            ns: dict[str, Any] = {}
            exec(cache_path.read_text(encoding="utf-8"), ns)
            return ns.get(ctx.name) or next(v for v in ns.values() if callable(v))
        while True:
            code = _agent.generate_code(ctx)
            if ctx.id:
                id_file = self._ids_dir / f"{ctx.id}.py"
                id_file.write_text(code, encoding="utf-8")
                if verbose:
                    print(
                        f"[autocode] Saved generated code to ID cache: {id_file}")
                frame = inspect.stack()[1]
                caller_path = Path(frame.filename).relative_to(Path.cwd())
                struct_dir = self._structure_dir / caller_path.parent
                struct_dir.mkdir(parents=True, exist_ok=True)
                struct_file = struct_dir / f"{ctx.name}.py"
                if struct_file.exists() or struct_file.is_symlink():
                    struct_file.unlink()
                struct_file.symlink_to(id_file.resolve())
                cache_path = id_file
            else:
                frame = inspect.stack()[1]
                caller_path = Path(frame.filename).relative_to(Path.cwd())
                struct_dir = self._structure_dir / caller_path.parent
                struct_dir.mkdir(parents=True, exist_ok=True)
                struct_file = struct_dir / f"{ctx.name}.py"
                struct_file.write_text(code, encoding="utf-8")
                if verbose:
                    print(
                        f"[autocode] Saved generated code to structure cache: {struct_file}")
                cache_path = struct_file
            if verbose:
                print("[autocode] Generated Code:\n", code)
            if interactive:
                print(code)
                ans = input("Accept generated code? (y/n): ").lower()
                if ans != "y":
                    if cache_path.exists():
                        cache_path.unlink()
                    feedback_text = input(
                        "Enter feedback on the code issues: ")
                    new_fb = HumanFeedback(
                        feedback=feedback_text, previous_code=code)
                    ctx.feedbacks.append(new_fb)
                    continue
            ns: dict[str, Any] = {}
            try:
                exec(code, ns)
                return ns.get(ctx.name) or next(v for v in ns.values() if callable(v))
            except Exception as e:
                error_fb = ErrorFeedback(error_message=str(e))
                ctx.feedbacks.append(error_fb)
                if interactive:
                    if cache_path.exists():
                        cache_path.unlink()
                    ans = input(
                        f"Execution error occurred: {e}. Do you want to retry? (y/n): ").lower()
                    if ans == "y":
                        continue
                    else:
                        raise
                if retry:
                    if cache_path.exists():
                        cache_path.unlink()
                    continue
                else:
                    raise


_default_assistant: Assistant = Assistant(
    verbose=False,
    interactive=False,
    retry=False,
    agent=OpenAIAgent(api_key=os.getenv("OPENAI_API_KEY")),
)


def setup_autocode(
    dotenv_path: str | None = None,
    verbose: bool = False,
    interactive: bool = False,
    retry: bool = False,
    agent: BaseAgent | None = None,
):
    global _default_assistant
    if dotenv_path:
        load_dotenv(dotenv_path)
    if agent is None:
        agent = OpenAIAgent(api_key=os.getenv("OPENAI_API_KEY"))
    _default_assistant = Assistant(
        verbose=verbose,
        interactive=interactive,
        retry=retry,
        agent=agent,
    )


def autocode(
    description: str,
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
    decorator: bool = False,
    verbose: bool = None,
    interactive: bool = None,
    retry: bool = None,
    agent: BaseAgent | None = None,
) -> Any:
    return _default_assistant.autocode(
        description,
        args,
        kwargs,
        use_extra_args,
        extra_args_type,
        use_extra_kwargs,
        extra_kwargs_type,
        return_type,
        name,
        id,
        tools,
        refs,
        override,
        verbose,
        interactive,
        retry,
        agent,
    )
