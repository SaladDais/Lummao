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

from lslopt import lslfuncs


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
        new_coord = []
        for i, axis_val in enumerate(sym_val):
            if i == member_idx:
                new_coord.append(new_val)
            else:
                new_coord.append(axis_val)
        new_sym_val = sym_val.__class__(tuple(new_coord))
    else:
        new_sym_val = new_val

    sym_scope[sym_name] = new_sym_val

    # Force an update of the locals array from locals dict (if we were dealing with a locals dict)
    # Only works if the locals dict is from the immediate caller!
    # We could remove this requirement by representing "locals" with a class that holds all locals,
    # but that'd be annoying, wouldn't it. On second thought, maybe we should.
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))

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


class BaseLSLScript:
    """TODO: some nice helper methods here"""
    pass
