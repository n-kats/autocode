from nk_autocode import autocode

my_add = autocode(
    "足し算", name="my_add",
    args=["a", "b"], return_type=int,
    interactive=True, verbose=True)
a = 5
b = 3
result = my_add(a, b)
print(f"Result of adding {a} and {b} is: {result}")
