from typing import Union

from .vendor.lslopt.lslfuncs import typecast, Quaternion, Vector, Key, cond, neg

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


def compile_script(lsl_contents: Union[str, bytes]) -> BaseLSLScript:
    """Compile an LSL script to a Python class, returning a class instance"""
    new_globals = globals().copy()
    exec(convert_script(lsl_contents), new_globals)
    return new_globals["Script"]()


def compile_script_file(path) -> BaseLSLScript:
    """Compile an LSL script file to a Python class, returning a class instance"""
    with open(path, "rb") as f:
        return compile_script(f.read())
