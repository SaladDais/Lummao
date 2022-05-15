import os
import sys

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
