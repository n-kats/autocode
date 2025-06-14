import subprocess
import tempfile


class Editor:
    def __init__(self, editor: str):
        self.__editor = editor

    def edit(self, code: str) -> tuple[bool, str]:
        """
        Edit code using an editor.

        Args:
            code (str): Code to edit
        Returns:
            tuple[bool, str]: Status of editing result (True if editing was performed) and code after editing
        """
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py") as f:
            f.write(code)
            f.flush()
            try:
                subprocess.check_call([self.__editor, f.name])
                f.seek(0)
                new_code = f.read()
                return True, new_code
            except subprocess.CalledProcessError:
                return False, code
