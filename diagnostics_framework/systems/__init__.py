"""Auto-discover and import all system modules so their decorators register on import."""
import importlib
import pkgutil
from pathlib import Path

_package_dir = Path(__file__).parent

for _finder, _name, _ispkg in pkgutil.iter_modules([str(_package_dir)]):
    importlib.import_module(f"{__name__}.{_name}")
