from nk_autodoc.framework import Context
from nk_autodoc.presets.compressors import Compressor
from nk_autodoc.presets.models import OpenAIModel
from nk_autodoc.presets.outputs import IOOutput
from nk_autodoc.presets.writers import Writer

writer = Writer(model=OpenAIModel("gpt-4.1"), context=Context(), output=IOOutput())
compressor = Compressor()
