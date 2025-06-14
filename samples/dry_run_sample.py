from nk_autocode import autocode, print_and_exception, return_value, setup_autocode

setup_autocode(dry_run=True)


@autocode(dry_run_fn=return_value(123, verbose=True), decorator=True)
def sample_function(x: int, y: int) -> int:
    """サンプル関数"""


@autocode(dry_run_fn=print_and_exception, decorator=True)
def another_sample_function(x: int, y: int) -> int:
    """別のサンプル関数"""


print("case 1")
print(sample_function(1, 2))  # Should print 123
print()
print("case 2")
try:
    another_sample_function(3, 4)
except Exception as e:
    print(f"Exception caught: {e}")
