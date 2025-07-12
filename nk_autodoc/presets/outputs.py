import sys
from io import TextIOBase
from pathlib import Path

from nk_autodoc.framework import BaseOutput


class FileOutput:
    def __init__(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        self.__file_obj = open(file_path, "w", encoding="utf-8")

    def print(self, text: str) -> None:
        self.__file_obj.write(text + "\n")


class IOOutput(BaseOutput):
    def __init__(self, io_stream: TextIOBase = sys.stdout):  # type: ignore
        self.__io_stream = io_stream

    def print(self, text: str) -> None:
        print(text, file=self.__io_stream)
