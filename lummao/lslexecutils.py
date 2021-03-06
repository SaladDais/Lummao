#    (C) Copyright 2022 Salad Dais. All rights reserved.
#
#    This is free software: you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    Lummao is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Lummao. If not, see <http://www.gnu.org/licenses/>.

"""
Wrappers for PyOptimizer's eval functionality, with reversed argument order for correct LSL
expression eval order
"""
import binascii
import ctypes
import struct
import sys
from typing import List, Sequence, Tuple, Any, Optional, Dict, Callable

from lslopt import lslfuncs, lslcommon

lslcommon.IsCalc = True


def assign(obj_dict: dict, name: str, val):
    """
    Assignment wrapper that can be used in expression context

    Walrus operator can't be used for attributes, so this is necessary in a number of cases
    """
    obj_dict[name] = val
    return val


def bin2float(_ignored: str, flt_str: str) -> float:
    """Convert binary form of a float to `float`. `_ignored` is only for readability."""
    return struct.unpack("f", binascii.unhexlify(flt_str))[0]


def radd(rhs, lhs, f32=True):
    return lslfuncs.add(lhs, rhs, f32)


def rsub(rhs, lhs, f32=True):
    return lslfuncs.sub(lhs, rhs, f32)


def rmul(rhs, lhs, f32=True):
    return lslfuncs.mul(lhs, rhs, f32)


def rdiv(rhs, lhs, f32=True):
    return lslfuncs.div(lhs, rhs, f32)


def rmod(rhs, lhs, f32=True):
    return lslfuncs.mod(lhs, rhs, f32)


def req(rhs, lhs):
    return lslfuncs.compare(lhs, rhs, True)


def rneq(rhs, lhs):
    return lslfuncs.compare(lhs, rhs, False)


def rless(rhs, lhs):
    return lslfuncs.less(lhs, rhs)


def rgreater(rhs, lhs):
    return lslfuncs.less(rhs, lhs)


def rleq(rhs, lhs):
    return int(not rgreater(rhs, lhs))


def rgeq(rhs, lhs):
    return int(not rless(rhs, lhs))


def rbooland(rhs, lhs):
    return int(bool(lhs and rhs))


def rboolor(rhs, lhs):
    return int(bool(lhs or rhs))


def rbitxor(rhs, lhs):
    return lslfuncs.S32(lhs ^ rhs)


def rbitor(rhs, lhs):
    return lslfuncs.S32(lhs | rhs)


def rbitand(rhs, lhs):
    return lslfuncs.S32(lhs & rhs)


def rshl(rhs, lhs):
    return lslfuncs.S32(lhs << (rhs & 31))


def rshr(rhs, lhs):
    # 99% sure this does sign-extension correctly
    return lslfuncs.S32(lhs >> (rhs & 31))


def bitnot(val):
    return lslfuncs.S32(~val)


def boolnot(val):
    return int(not val)


def replace_coord_axis(coord_val, member_idx, new_val):
    new_coord = []
    for i, axis_val in enumerate(coord_val):
        if i == member_idx:
            new_coord.append(new_val)
        else:
            new_coord.append(axis_val)
    return coord_val.__class__(tuple(new_coord))


def prepostincrdecr(sym_scope, sym_name, mod_amount, post, member_idx, frame):
    """
    ++i, --i, i++, i--, vec.x++, and so on.

    Post-increment in particular doesn't exist in python, so we fake it.
    """
    sym_val = sym_scope[sym_name]
    if member_idx:
        orig_val = sym_val[member_idx]
    else:
        orig_val = sym_val
    new_val = radd(orig_val, mod_amount)

    if member_idx:
        new_sym_val = replace_coord_axis(sym_val, member_idx, sym_val[member_idx] + mod_amount)
    else:
        new_sym_val = new_val

    sym_scope[sym_name] = new_sym_val

    # Force an update of the locals array from locals dict (if we were dealing with a locals dict)
    # Only works if the locals dict is from the immediate caller!
    # We could remove this requirement by representing "locals" with a class that holds all locals,
    # but that'd be annoying, wouldn't it. On second thought, maybe we should.
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))

    # Return the original val for post assignments, in either event this will return the value of
    # the member itself if this was a vector or quat member assignment.
    if post:
        return orig_val
    return new_val


def preincr(sym_scope, sym_name, member_idx=None):
    return prepostincrdecr(sym_scope, sym_name, 1, False, member_idx, sys._getframe(1))  # noqa


def postincr(sym_scope, sym_name, member_idx=None):
    return prepostincrdecr(sym_scope, sym_name, 1, True, member_idx, sys._getframe(1))  # noqa


def predecr(sym_scope, sym_name, member_idx=None):
    return prepostincrdecr(sym_scope, sym_name, -1, False, member_idx, sys._getframe(1))  # noqa


def postdecr(sym_scope, sym_name, member_idx=None):
    return prepostincrdecr(sym_scope, sym_name, -1, True, member_idx, sys._getframe(1))  # noqa


class StateChangeException(Exception):
    """Signal that the state should change, unwinding the stack"""
    def __init__(self, new_state: str):
        self.new_state = new_state


class CallableCollection(Dict[str, Callable]):
    def __getattr__(self, item):
        return self[item]


class BaseLSLScript:
    def __init__(self):
        self.current_state: str = "default"
        self.next_state: Optional[str] = None
        self.event_queue: List[Tuple[str, Sequence[Any]]] = [("state_entry", ())]
        self.builtin_funcs: CallableCollection = CallableCollection()
        # Stuff all the builtins we have functions for into a big ol dict where they can be replaced
        for func_name in dir(lslfuncs):
            if not func_name.startswith("ll"):
                continue
            val = getattr(lslfuncs, func_name)
            if not callable(val):
                continue
            self.builtin_funcs[func_name] = val

    def queue_event(self, event_name: str, args: Sequence[Any]):
        self.event_queue.append((event_name, args))

    def _trigger_event_handler(self, name: str, *args):
        # TODO: need extras for things like llDetectedKey(num)
        func = getattr(self, f"e{self.current_state}{name}", None)
        if func is not None:
            func(*args)

    def execute_one(self):
        event, event_args = self.event_queue.pop(0)
        try:
            self._trigger_event_handler(event, *event_args)
            # TODO: Check this is correct, is changing state in state_exit possible?
            if event == "state_exit":
                # Need to queue a state_entry for the new state
                self.current_state = self.next_state
                self.event_queue.append(("state_entry", ()))

        except StateChangeException as e:
            self.next_state = e.new_state
            self.event_queue.clear()
            self.event_queue.append(("state_exit", ()))

    def execute(self):
        while self.event_queue:
            self.execute_one()
