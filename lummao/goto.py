"""
Very, very basic `goto` support for Python that works on Python 3.11+

Only works with Lummao generated code, it doesn't attempt to support
`for` loops, `try` / `except`, or `with` at all. I'm not convinced
such a thing would be realistic or desirable :)

License: CC0 / MIT / 0-BSD / whatever.
"""
import sys
import types
import functools
import weakref
from typing import Sequence, Generator, Dict, List

import bytecode


# use a weak dictionary in case code objects can be garbage-collected
_patched_code_cache = weakref.WeakKeyDictionary()


def _find_opcode_sequences(bc: bytecode.Bytecode, opcode_names: Sequence[str]) -> Generator[int, None, None]:
    for i in range(len(bc) - len(opcode_names) + 1):
        valid = True
        for name, instr in zip(opcode_names, bc[i:i + len(opcode_names)]):
            if name is None or instr is None:
                valid = False
                break
            if getattr(instr, 'name', None) != name:
                valid = False
                break
        if valid:
            yield i


def _find_labels(bc: bytecode.Bytecode) -> Dict[str, int]:
    labels = {}
    for idx in _find_opcode_sequences(bc, ['LOAD_GLOBAL', 'LOAD_ATTR', 'POP_TOP']):
        load_attr_arg = bc[idx].arg
        if isinstance(load_attr_arg, tuple):
            load_attr_arg = load_attr_arg[1]
        if load_attr_arg != "label":
            continue
        label_name = bc[idx + 1].arg
        if label_name in labels:
            raise ValueError(f"{label_name!r} already in labels list")
        labels[label_name] = idx
    return labels


def _find_jumps(bc: bytecode.Bytecode) -> Dict[str, List[int]]:
    jumps = {}
    for idx in _find_opcode_sequences(bc, ['LOAD_GLOBAL', 'LOAD_ATTR', 'POP_TOP']):
        load_attr_arg = bc[idx].arg
        if isinstance(load_attr_arg, tuple):
            load_attr_arg = load_attr_arg[1]
        if load_attr_arg != "goto":
            continue
        label_name = bc[idx + 1].arg
        if label_name not in jumps:
            jumps[label_name] = []
        jumps[label_name].append(idx)
    return jumps


def _patch_code(code):
    new_code = _patched_code_cache.get(code)
    if new_code is not None:
        return new_code

    bc = bytecode.Bytecode.from_code(code)
    labels = _find_labels(bc)
    jumps = _find_jumps(bc)

    missing_labels = jumps.keys() - labels.keys()
    if missing_labels:
        raise ValueError(f"Missing labels for jumps to {missing_labels}")

    label_instances = {name: bytecode.Label() for name in labels}
    for label_name, label_offset in labels.items():
        location = bc[label_offset].location
        lineno = bc[label_offset].lineno
        # Fill with nops so coverage still works
        for i in range(3):
            bc[label_offset + i] = bytecode.Instr(name="NOP", location=location, lineno=lineno)
        bc[label_offset + 2] = label_instances[label_name]

    for label_name, jump_offsets in jumps.items():
        for jump_offset in jump_offsets:
            location = bc[jump_offset].location
            lineno = bc[jump_offset].lineno
            # Fill with nops so coverage still works
            for i in range(3):
                bc[jump_offset + i] = bytecode.Instr(name="NOP", location=location, lineno=lineno)

            if sys.version_info < (3, 11):
                jump_name = "JUMP_ABSOLUTE"
            elif jump_offset > labels[label_name]:
                jump_name = "JUMP_BACKWARD_NO_INTERRUPT"
            else:
                jump_name = "JUMP_FORWARD"

            bc[jump_offset + 2] = bytecode.Instr(
                name=jump_name,
                arg=label_instances[label_name],
                location=location
            )

    new_code = bc.to_code()
    _patched_code_cache[code] = new_code
    return new_code


def with_goto(func_or_code):
    if isinstance(func_or_code, types.CodeType):
        return _patch_code(func_or_code)

    return functools.update_wrapper(
        types.FunctionType(
            _patch_code(func_or_code.__code__),
            func_or_code.__globals__,
            func_or_code.__name__,
            func_or_code.__defaults__,
            func_or_code.__closure__,
        ),
        func_or_code
    )


class _CatchAll:
    __slots__ = []

    def __getattr__(self, item):
        raise RuntimeError("Unpatched goto for " + item)


# Not strictly necessary, but stops linters from freaking out.
label = _CatchAll()
goto = _CatchAll()
