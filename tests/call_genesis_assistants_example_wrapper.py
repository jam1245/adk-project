"""Wrapper module to expose ``call_assistant`` from the hyphen‑named file.

The original helper resides in ``tests/call-genesis-assistants-example.py`` –
the hyphens make it an invalid Python module name, so a direct import such as
``import call-genesis-assistants-example`` fails.  This wrapper uses
``importlib`` to load the file at runtime and re‑exports the ``call_assistant``
function under a valid module name.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Callable

_MODULE_PATH = os.path.join(os.path.dirname(__file__), "call-genesis-assistants-example.py")

def _load_module() -> Callable:
    spec = importlib.util.spec_from_file_location("call_assistant_module", _MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, "call_assistant"):
        raise AttributeError("Loaded module does not define 'call_assistant'")
    return getattr(module, "call_assistant")

# Export the function so that other code can simply ``from .call_genesis_assistants_example_wrapper import call_assistant``
call_assistant = _load_module()

__all__ = ["call_assistant"]
