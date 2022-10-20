import os
import sys
from typing import Union

try:
    # LSL-PyOptimizer isn't packaged, so it's a pain in the ass to include as a library.
    # Let's assume sanity first.
    import lslopt
except ImportError:
    # Ok, insanity. Get a manually specified path for LSL-PyOptimizer from the environment and try
    # to inject it into the PYTHONPATH so its module can be resolved at import.
    _pyoptimizer_path = os.environ.get("LSL_PYOPTIMIZER_PATH")
    if not _pyoptimizer_path:
        raise RuntimeError("LSL_PYOPTIMIZER_PATH environment variable must be set to PyOptimizer's path")
    if _pyoptimizer_path in sys.path:
        raise RuntimeError("LSL-PyOptimizer path already in PYTHONPATH, but lslopt module not found")
    sys.path.append(_pyoptimizer_path)
    import lslopt


from lslopt.lslfuncs import typecast, Quaternion, Vector, Key, cond, neg

from .lslexecutils import *
from .goto import with_goto, label, goto
from .exceptions import CompileError
import lummao._compiler as compiler_mod  # noqa


def convert_script(lsl_contents: Union[str, bytes]) -> bytes:
    """Convert an LSL script to a Python script, returning the Python text"""
    if isinstance(lsl_contents, str):
        lsl_bytes = lsl_contents.encode("utf8")
    else:
        lsl_bytes = lsl_contents
    return compiler_mod.lsl_to_python_src(lsl_bytes)


def convert_script_file(path) -> bytes:
    """Convert an LSL script file to a Python script, returning the Python text"""
    with open(path, "rb") as f:
        return convert_script(f.read())


def compile_script(lsl_contents: Union[str, bytes]):
    """Compile an LSL script to a Python class, returning a class instance"""
    new_globals = globals().copy()
    exec(convert_script(lsl_contents), new_globals)
    return new_globals["Script"]()


def compile_script_file(path):
    """Compile an LSL script file to a Python class, returning a class instance"""
    with open(path, "rb") as f:
        return compile_script(f.read())
