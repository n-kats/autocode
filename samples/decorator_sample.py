from nk_autocode import autocode, setup_autocode

setup_autocode(verbose=True, interactive=True, regenerate=True)

@autocode(decorator=True)
def my_add(a: int, b: int) -> int:
    """Perform addition of two integers."""


print("1 + 2 =", my_add(1, 2))
