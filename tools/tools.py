import importlib
import pkgutil
from pathlib import Path

from .tool import Tool

_PACKAGE_DIR = Path(__file__).parent
_EXCLUDED_MODULES = {"tool", "tools"}

tools = []

for module_info in pkgutil.iter_modules([str(_PACKAGE_DIR)]):
    module_name = module_info.name
    if module_name in _EXCLUDED_MODULES:
        continue

    module = importlib.import_module(f"tools.{module_name}")

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, Tool):
            tools.append(attr)
