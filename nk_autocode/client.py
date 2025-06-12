from abc import ABC
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel


class Variable(BaseModel):
    name: str
    type: Any | None = None
    default: str | None
    description: str | None


class Tool(BaseModel):
    pass


class Refference(BaseModel):
    pass


class GenerationContext(BaseModel):
    name: str | None
    description: str | None
    docstring: str | None
    args: list[Variable] | None
    kwargs = list[Variable] | None
    use_extra_args: bool
    extra_args_type: BaseModel | None
    use_extra_kwargs: bool
    extra_kwargs_type: BaseModel | None
    return_type: BaseModel | None
    tools: list[Tool]
    refs: list[Refference]


class CodeGenerator(ABC):
    def generate_code(
        self,
        context: GenerationContext,
    ) -> str:
        pass

    def fix_code(
        self,
        previous_code: str,
        error: Exception,
        context: GenerationContext,
    ) -> str:
        pass


class Workspace:
    def __init__(self, root_dir: Path, generating_dir: Path):
        self.__root_dir = root_dir
        self.__generating_dir = generating_dir
        self.__prompt_dir = prompt_dir


class AutocodeAgent:
    def __init__(self, workspace: Workspace, code_generator: CodeGenerator | None = None):
        self.workspace = workspace
        self.code_generator = code_generator

    def generate_code(self, context: GenerationContext) -> str:
        if self.code_generator:
            return self.code_generator.generate_code(context)
        raise NotImplementedError("Code generator is not set.")

    def _try_retrieve_code(self, package_and_function: str) -> str:
        module_path, func_name = path.split(":")
        module = importlib.import_module(module_path)
        return getattr(module, func_name, None)


global_agent = None


def setup_autocode(
    dotenv_path: str | Path | None = None,
    verbose: bool = False,
    interactive: bool = False,
    retry: bool = False,
    code_generator: CodeGenerator | None = None,
):
    if dotenv_path:
        load_dotenv(dotenv_path)
    global global_agent

    global_agent = AutocodeAgent(
        workspace=Workspace(
            root_dir=Path.cwd(),
            generating_dir=Path.cwd() / "generated",
        ),
        code_generator=code_generator,
    )


def autocode(
    description=None,
    docstring=None,
    args=None,
    kwargs=None,
    use_extra_args=False,
    extra_args_type=None,
    use_extra_kwargs=False,
    extra_kwargs_type=None,
    return_type=None,
    name=None,
    id=None,
    tools=None,
    refs=None,
    override=None,
    decorator=False,
    verbose=None,
    interactive=None,
    retry=None,
):
    if global_agent is None:
        raise RuntimeError("Autocode agent is not set up. Please call setup_autocode() first.")

    context = GenerationContext(
        name=name,
        description=description,
        docstring=docstring,
        args=args or [],
        kwargs=kwargs or [],
        use_extra_args=use_extra_args,
        extra_args_type=extra_args_type,
        use_extra_kwargs=use_extra_kwargs,
        extra_kwargs_type=extra_kwargs_type,
        return_type=return_type,
        tools=tools or [],
        refs=refs or [],
    )

    return global_agent.generate_code(context)
