from uuid import uuid4
from nk_autocode import autocode, setup_autocode
import inspect

setup_autocode(verbose=True, interactive=True, regenerate=True)
id_= str(uuid4())
add_code = autocode("足し算", name="my_add", args=["a", "b"], return_type=int, id=id_)
print("1 + 2 =", add_code(1, 2))
setup_autocode(regenerate=False)
add_code = autocode("足し算", name="my_add", args=["a", "b"], return_type=int, id=id_)
print("1 + 2 =", add_code(1, 2))
