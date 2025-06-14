import functools
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from nk_autocode.editor import Editor
from nk_autocode.framework import (
    BaseAgent,
    BaseAssistant,
    BaseGeneratedCode,
    CachedCode,
    CompiledCode,
    Context,
    DecoratorCode,
    DryRunCode,
    ErrorFeedback,
    Feedback,
    GiveUpGenerationError,
    HumanFeedback,
    ImportedCode,
    Variable,
)


@dataclass
class Workspace:
    cache_root: Path

    def get_code_path_by_path(self, path: Path, name: str) -> Path:
        struct_dir = self.cache_root / "structure"
        struct_file = struct_dir / f"{path}/{name}.py"
        return struct_file

    def get_code_path_by_id(self, id: str) -> Path | None:
        ids_dir = self.cache_root / "ids"
        id_file = ids_dir / f"{id}.py"
        if id_file.is_file():
            return id_file
        return None

    def save_code_by_id(self, id: str, code: str, verbose: bool = False) -> Path:
        ids_dir = self.cache_root / "ids"
        ids_dir.mkdir(parents=True, exist_ok=True)
        id_file = ids_dir / f"{id}.py"
        id_file.write_text(code, encoding="utf-8")
        if verbose:
            print(f"Code saved to {id_file}")
        return id_file

    def save_code_by_name(self, name: str, code: str, verbose: bool = False) -> Path:
        struct_dir = self.cache_root / "structure"
        struct_dir.mkdir(parents=True, exist_ok=True)
        struct_file = struct_dir / f"{name}.py"
        struct_file.write_text(code, encoding="utf-8")
        if verbose:
            print(f"Code saved to {struct_file}")
        return struct_file

    def save_code(
        self,
        code: str,
        id_: str | None = None,
        name: str | None = None,
        caller_path: Path | None = None,
        verbose: bool = False,
    ) -> None:
        if id_:
            self.save_code_by_id(id_, code, verbose=verbose)
        elif name:
            self.save_code_by_name(name, code, verbose=verbose)
        else:
            raise ValueError("Either 'id' or 'name' must be provided for saving code.")


def load_cached_code(
    workspace: Workspace,
    caller_path: Path | None,
    name: str | None = None,
    id_: str | None = None,
    verbose: bool = False,
) -> tuple[bool, BaseGeneratedCode | None]:
    cache_path: Path | None = None
    if id_:
        id_file = workspace.get_code_path_by_id(id_)
        if id_file and id_file.is_file():
            cache_path = id_file
    if not cache_path and caller_path and name:
        struct_file = workspace.get_code_path_by_path(caller_path, name)
        if struct_file.is_file():
            cache_path = struct_file
    if cache_path:
        if verbose:
            print(f"[autocode] Loaded code from cache: {cache_path}")
        ns: dict[str, Any] = {}
        exec(cache_path.read_text(encoding="utf-8"), ns)
        func = ns.get(name) if name else None
        if not func:
            func = next((v for v in ns.values() if callable(v)), None)
        if func:
            return True, CachedCode(func, str(cache_path))
    return False, None


def save_code(workspace: Workspace, name: str, code: str, id: str | None = None) -> Path:
    if id:
        return workspace.save_code_by_id(id, code)
    else:
        return workspace.save_code_by_name(name, code)


class Assistant(BaseAssistant):
    def __init__(
        self,
        verbose: bool,
        interactive: bool,
        regenerate: bool,
        agent: BaseAgent,
        editor: Editor | None,
        dry_run: bool | None = None,
        dry_run_fn: Callable | None = None,
    ):
        self.__verbose = verbose
        self.__interactive = interactive
        self.__regenerate = regenerate
        self.__agent = agent
        self.__dry_run = dry_run if dry_run is not None else False
        self.__workspace = Workspace(Path("_cache/autocode"))
        self.__editor = editor

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
        dry_run_fn: Callable | None = None,
    ) -> BaseGeneratedCode:
        if dry_run is None:
            dry_run = self.__dry_run
        if dry_run:
            if dry_run_fn is None:
                raise ValueError("dry_run_fn must be provided for dry run.")
            if decorator:

                def decorator_func(func: Callable) -> DecoratorCode:
                    @functools.wraps(func)
                    def wrapper(*args: Any, **kwargs: Any) -> Any:
                        return dry_run_fn(*args, **kwargs)

                    return DecoratorCode(wrapper, func.__name__)

                return decorator_func  # type: ignore
            else:
                return DryRunCode(dry_run_fn, description)

        if stack is None:
            stack = inspect.stack()[1:]
        if override:
            try:
                mod, fn = override.rsplit(":", 1)
                module = __import__(mod, fromlist=[fn])
                func = getattr(module, fn)
                return ImportedCode(func, mod, module.__file__ or "")
            except (ImportError, AttributeError):
                pass

        # デフォルト設定を上書きする
        if agent is None:
            agent = self.__agent
        if regenerate is None:
            regenerate = self.__regenerate
        if verbose is None:
            verbose = self.__verbose
        if interactive is None:
            interactive = self.__interactive

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
            stack=stack,
        )
        _agent = agent or self.__agent
        caller_path = (
            Path(stack[0].filename).relative_to(Path.cwd()) if stack else None
        )  # TODO: 本当はcwdではなく、プロジェクトのルートディレクトリを使うべき
        if decorator:
            return self._autocode_decorator(
                ctx, _agent, verbose=verbose, interactive=interactive, regenerate=regenerate, caller_path=caller_path
            )  # type: ignore
        return self._generate_from_context(
            ctx,
            _agent,
            verbose=verbose,
            interactive=interactive,
            regenerate=regenerate,
            caller_path=caller_path,
            id_=id,
        )

    def _generate_from_context(
        self,
        ctx: Context,
        agent: BaseAgent,
        verbose: bool,
        interactive: bool,
        regenerate: bool,
        caller_path: Path | None,
        id_: str | None = None,
    ) -> BaseGeneratedCode:
        if not regenerate:
            success, loaded_code = load_cached_code(
                self.__workspace, name=ctx.name, id_=ctx.id, caller_path=caller_path, verbose=verbose
            )
            if success and loaded_code:
                return loaded_code

        while True:
            code = agent.generate_code(ctx, verbose=verbose)
            if verbose and not interactive:
                print("[autocode] Generated Code:\n", code)

            success = True
            feedback: Feedback | None = None

            if interactive:
                code, success, feedback = self._human_check(code)

            if success:
                success, feedback = self._error_check(code, ctx.name, verbose=verbose)

            if success:
                break

            if not yes_no_prompt("Regenerate code?"):
                raise GiveUpGenerationError("User chose to give up code generation.")
            if feedback:
                ctx.feedbacks.append(feedback)

        self.__workspace.save_code(code=code, id_=id_, name=ctx.name, caller_path=caller_path, verbose=verbose)
        func = compile_code(code, ctx.name)
        return CompiledCode(func, code, ctx)

    def _autocode_decorator(
        self,
        ctx: Context,
        _agent: BaseAgent,
        verbose: bool,
        interactive: bool,
        regenerate: bool,
        caller_path: Path | None,
    ) -> Callable:
        def decorator(func: Callable) -> BaseGeneratedCode:
            ctx_copy = ctx.copy()
            ctx_copy.name = func.__name__
            ctx_copy.docstring = func.__doc__

            return self._generate_from_context(
                ctx_copy,
                _agent,
                verbose=verbose,
                interactive=interactive,
                regenerate=regenerate,
                caller_path=caller_path,
                id_=ctx.id,
            )

        return decorator

    def _human_check(self, code: str) -> tuple[str, bool, HumanFeedback | None]:
        is_generated = True
        while True:
            if is_generated:
                print("[autocode] Generated Code:")
                print(code)
                command = select_prompt(
                    "Accept generated code(y/n)? Or edit it(e)?",
                    ["y", "n", "e"],
                )
            else:
                print("[autocode] Editted Code:")
                print(code)
                command = select_prompt(
                    "Accept code(y/n)? Or edit it(e)?",
                    ["y", "n", "e"],
                )
            if command == "y":
                return code, True, None
            elif command == "e":
                if self.__editor is None:
                    print("[autocode] No editor configured. Cannot edit code.")
                    continue
                editted, fixed_code = self.__editor.edit(code)
                if editted:
                    is_generated = False
                    code = fixed_code
                continue
            else:
                feedback_text = input("Enter feedback on the code issues: ")
                return code, False, HumanFeedback(feedback=feedback_text, previous_code=code)

    def _error_check(self, code: str, function_name: str | None, verbose: bool) -> tuple[bool, ErrorFeedback | None]:
        try:
            created_function = compile_code(code, function_name)
            if created_function is None:
                if function_name is None:
                    if verbose:
                        print("[autocode] No function found in the generated code.")
                    return False, ErrorFeedback(error_message="No function found in the code.", previous_code=code)
                else:
                    if verbose:
                        print(f"[autocode] Function '{function_name}' not found in the generated code.")
                    return False, ErrorFeedback(
                        error_message=f"Function '{function_name}' not found in the code.", previous_code=code
                    )
            elif not callable(created_function):
                if verbose:
                    print(f"[autocode] '{function_name}' is not callable.")
                return False, ErrorFeedback(error_message=f"'{function_name}' is not callable.", previous_code=code)
            else:
                return True, None
        except Exception as e:
            if verbose:
                print(f"[autocode] Error executing generated code: {e}")
            return False, ErrorFeedback(error_message=str(e), previous_code=code)


def compile_code(code: str, function_name: str | None) -> Any:
    ns: dict[str, Any] = {}
    exec(code, ns)
    if function_name is None:
        return next((v for v in ns.values() if callable(v)), None)
    else:
        return ns.get(function_name)


def select_prompt(prompt: str, options: list[str]) -> str:
    message = f"{prompt} ({', '.join(options)})"
    while True:
        ans = input(message).strip().lower()
        if ans in options:
            return ans
        else:
            print(f"Please choose from {', '.join(options)}.", file=sys.stderr)


def yes_no_prompt(prompt: str) -> bool:
    return select_prompt(prompt, ["y", "n"]) == "y"
