from nk_autocode import autocode, setup_autocode

setup_autocode(verbose=True, interactive=True, regenerate=True)

print_args = autocode(
    "引数の表示",
    name="print_args",
    args=[{"var": "a", "type": int}, {"var": "b", "type": "int"}],
    use_extra_args=True,
    extra_args_type=str,
    use_extra_kwargs=True,
    extra_kwargs_type=bool,
    return_type=None,
)
print_args(1, 2, "extra_arg", extra_kwarg=True)
