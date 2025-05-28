import os
import uuid
import inspect
import re
import openai
from dotenv import load_dotenv

# Configuration class for global settings
default_model = "gpt-4.1"
class _Config:
    def __init__(self):
        self.dotenv_path = None
        self.verbose = False
        self.interactive = False
        self.retry = False

config = _Config()


def setup_autocode(dotenv_path=None, verbose=False, interactive=False, retry=False):
    """
    Initialize autocode configuration.

    Args:
        dotenv_path (str): Path to .env file containing OPENAI_API_KEY.
        verbose (bool): If True, print prompts and generated code.
        interactive (bool): If True, prompt user to accept code interactively.
        retry (bool): If True, retry generation on errors.
    """
    if dotenv_path:
        load_dotenv(dotenv_path)
        config.dotenv_path = dotenv_path
    openai.api_key = os.getenv("OPENAI_API_KEY")
    config.verbose = verbose
    config.interactive = interactive
    config.retry = retry


def autocode(
    description=None,
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
    """
    Generate or wrap a function based on a description and signature.

    Usage forms:
    - Direct generation: fn = autocode("desc", args=[...], ...)
    - Decorator: @autocode(decorator=True)
      def fn(a, b): ...

    See README for full API.
    """
    # Merge local overrides with global config
    _verbose = verbose if verbose is not None else config.verbose
    _interactive = interactive if interactive is not None else config.interactive
    _retry = retry if retry is not None else config.retry

    if decorator:
        def _decorate(func):
            desc = (func.__doc__.strip() if func.__doc__ else description) or func.__name__
            params = list(inspect.signature(func).parameters.keys())
            generated = _generate_function(
                desc, params, kwargs, use_extra_args, extra_args_type,
                use_extra_kwargs, extra_kwargs_type, return_type,
                name or func.__name__, id, tools, refs, override,
                _verbose, _interactive, _retry
            )
            return generated
        return _decorate

    # Direct generation path
    _args = args or []
    generated = _generate_function(
        description, _args, kwargs, use_extra_args, extra_args_type,
        use_extra_kwargs, extra_kwargs_type, return_type,
        name, id, tools, refs, override,
        _verbose, _interactive, _retry
    )
    return generated


def _build_prompt(
    description, args, kwargs, use_extra_args, extra_args_type,
    use_extra_kwargs, extra_kwargs_type, return_type, name, id, tools, refs, override
):
    """
    Build the system/user prompt for OpenAI based on settings.
    """
    prompt = "### Function Description\n" + (description or "No description provided") + "\n\n"
    if name:
        prompt = f"### Function Name\n{name}\n\n" + prompt
    if id:
        prompt = f"### ID: {id}\n\n" + prompt
    # Parameters
    prompt += "### Parameters\n"
    for arg in args or []:
        if isinstance(arg, dict):
            var = arg['var']; argtype = arg.get('type', 'Any').__name__
            default = arg.get('default')
            prompt += f"- {var}: {argtype}"
            if default is not None: prompt += f" = {default}"
            prompt += "\n"
        else:
            prompt += f"- {arg}: Any\n"
    if use_extra_args:
        etype = extra_args_type.__name__ if extra_args_type else "Any"
        prompt += f"- *args: {etype}\n"
    if kwargs:
        for kw in kwargs:
            if isinstance(kw, dict):
                var = kw['var']; ktype = kw.get('type', 'Any').__name__
                default = kw.get('default')
                prompt += f"- {var}: {ktype}"
                if default is not None: prompt += f" = {default}"
                prompt += "\n"
            else:
                prompt += f"- {kw}: Any\n"
    if use_extra_kwargs:
        ktype = extra_kwargs_type.__name__ if extra_kwargs_type else "Any"
        prompt += f"- **kwargs: {ktype}\n"
    if return_type:
        rtype = return_type.__name__
        prompt += "\n### Returns\n" + rtype + "\n"
    if override:
        prompt += f"\n# Override existing: {override}\n"
    # Tools and refs can be appended similarly if needed
    return prompt


def _generate_function(
    description, args, kwargs, use_extra_args, extra_args_type,
    use_extra_kwargs, extra_kwargs_type, return_type, name, id,
    tools, refs, override, verbose, interactive, retry
):
    prompt = _build_prompt(
        description, args, kwargs, use_extra_args, extra_args_type,
        use_extra_kwargs, extra_kwargs_type, return_type,
        name, id, tools, refs, override
    )
    if verbose:
        print("[autocode] Prompt:\n", prompt)

    while True:
        response = openai.chat.completions.create(
            model=default_model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        text = response.choices[0].message.content
        code = extract_code(text)
        if verbose:
            print("[autocode] Generated Code:\n", code)
        if interactive:
            print(code)
            ans = input("Accept generated code? (y/n): ").lower()
            if ans != 'y':
                continue
        # Execute
        namespace = {}
        try:
            exec(code, namespace)
            # Retrieve the generated function
            fn = None
            if name and name in namespace:
                fn = namespace[name]
            else:
                # pick first callable
                fn = next(v for v in namespace.values() if callable(v))
        except Exception as e:
            if retry:
                print(f"[autocode] Execution error: {e}. Retrying...")
                continue
            else:
                raise
        return fn


def extract_code(text):
    """
    Extract Python code block from model response.
    """
    m = re.search(r"```(?:python)?\n(.*?)(?:```|$)", text, re.S)
    return m.group(1).strip() if m else text.strip()

