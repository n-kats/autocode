import importlib.metadata

from nk_autocode.presets.default import autocode, setup_autocode

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"
