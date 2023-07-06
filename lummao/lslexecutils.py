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
import abc
import asyncio
import binascii
import contextlib
import ctypes
import dataclasses
import functools
import struct
import sys
import time
import uuid
import weakref
from typing import List, Sequence, Tuple, Any, Optional, Dict, Callable, Set, Coroutine

from .vendor.lslopt import lslfuncs, lslcommon

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
    if member_idx is not None:
        orig_val = sym_val[member_idx]
    else:
        orig_val = sym_val
    new_val = radd(orig_val, mod_amount)

    if member_idx is not None:
        new_sym_val = replace_coord_axis(sym_val, member_idx, sym_val[member_idx] + mod_amount)
    else:
        new_sym_val = new_val

    if sys.version_info >= (3, 11) and sym_scope == frame.f_locals:
        # Python 3.11+ is special and needs to be convinced that locals should be
        # mutable via the locals() dict.
        ctypes.pythonapi.PyFrame_GetLocals(ctypes.py_object(frame))

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


def _make_async(func):
    """Make a normally synchronous function `await`able"""
    if asyncio.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def _wrapper(*args, **kwargs):
        val = func(*args, **kwargs)
        if asyncio.iscoroutine(val) or asyncio.isfuture(val):
            return await val
        return val
    return _wrapper


class BuiltinsCollection(Dict[str, Callable]):
    def __init__(self):
        super().__init__()
        # Stuff all the builtins we have functions for into a big ol dict where they can be replaced
        for func_name in dir(lslfuncs):
            if not func_name.startswith("ll"):
                continue
            val = getattr(lslfuncs, func_name)
            if not callable(val):
                continue
            self[func_name] = val

    def __setitem__(self, key, value):
        # All function calls in Lummao need to be async, but most of the
        # builtin functions are not actually implemented as coroutines.
        # Wrap everything that comes out of this collection through the `.`
        # accessor in a coroutine that makes it `await`able if it's not
        # already a coroutine.
        value = _make_async(value)
        super().__setitem__(key, value)

    def __getattr__(self, item):
        return self[item]


@dataclasses.dataclass
class DetectedDetails:
    Key: lslcommon.Key = lslcommon.Key(uuid.UUID(int=0))
    Owner: lslcommon.Key = lslcommon.Key(uuid.UUID(int=0))
    Group: lslcommon.Key = lslcommon.Key(uuid.UUID(int=0))
    Name: str = ""
    Pos: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    Vel: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    Rot: lslcommon.Quaternion = dataclasses.field(default_factory=lambda: lslcommon.Quaternion((0, 0, 0, 1)))
    LinkNumber: int = 0
    TouchFace: int = 0
    Type: int = 0
    TouchNormal: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    TouchBinormal: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    TouchPos: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    TouchST: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    TouchUV: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))
    Grab: lslcommon.Vector = dataclasses.field(default_factory=lambda: lslcommon.Vector((0, 0, 0)))


class BaseLSLScript:
    def __init__(self):
        self.current_state: str = "default"
        self.next_state: Optional[str] = None
        self.detected_stack: List[DetectedDetails] = []
        self.event_queue: List[Tuple[str, Sequence[Any], List[DetectedDetails]]] = [("state_entry", (), [])]
        # Things that may publish to the event queue asynchronously
        self.event_publishers: weakref.WeakKeyDictionary[Any] = weakref.WeakKeyDictionary()
        self.builtin_funcs = BuiltinsCollection()
        # Patch llDetected* builtins so that they return details related to the current event
        for field in dataclasses.fields(DetectedDetails):
            self.builtin_funcs['llDetected' + field.name] = self._make_detected_wrapper(field.name)

    @property
    def active_publishers(self) -> bool:
        return bool(sum(self.event_publishers.values()))

    def _make_detected_wrapper(self, detected_name: str) -> Callable[[int], Any]:
        def _wrapper(num: int):
            try:
                details = self.detected_stack[num]
            except IndexError:
                details = DetectedDetails()
            return getattr(details, detected_name)
        return _wrapper

    def queue_event(
            self,
            event_name: str,
            args: Sequence[Any],
            detected_stack: Optional[List[DetectedDetails]] = None
    ):
        self.event_queue.append((event_name, args, detected_stack or []))

    async def _trigger_event_handler(self, name: str, *args, detected_stack):
        # TODO: need extras for things like llDetectedKey(num)
        func = getattr(self, f"e{self.current_state}{name}", None)
        if func is not None:
            self.detected_stack = detected_stack
            try:
                await func(*args)
            finally:
                self.detected_stack = []

    async def execute_one(self):
        """Execute a single event from the event queue"""
        event, event_args, detected_stack = self.event_queue.pop(0)
        try:
            await self._trigger_event_handler(event, *event_args, detected_stack=detected_stack)
            # TODO: Check this is correct, is changing state in state_exit possible?
            if event == "state_exit":
                # Need to queue a state_entry for the new state
                self.current_state = self.next_state
                self.next_state = None
                self.event_queue.clear()
                self.event_queue.append(("state_entry", (), []))

        except StateChangeException as e:
            self.next_state = e.new_state
            # Switching states blows away the event stack
            self.event_queue.clear()
            self.event_queue.append(("state_exit", (), []))

    async def execute(self) -> bool:
        """Execute all events on the event queue"""
        handled = False
        while self.event_queue:
            handled = True
            await self.execute_one()
        return handled

    async def execute_until_complete(self) -> bool:
        """Execute until all background publishers are complete"""
        handled = False
        while self.active_publishers or self.event_queue:
            handled = await self.execute() or handled

            # We have async things running in the BG that may push to the event queue,
            # wait around a bit and try processing the event queue again.
            if self.active_publishers:
                await asyncio.sleep(0.0001)
        return handled


class ScriptExtender(abc.ABC):
    """Base class for something that extends a single script, modifying its environment"""
    script: Optional[BaseLSLScript]

    def __init__(self):
        self.script = None

    @abc.abstractmethod
    def extend_script(self, script: BaseLSLScript):
        """Should only be called once, with a single script instance"""
        if self.script:
            raise RuntimeError("Extender already bound to a script")
        self.script = script

    def register_publisher(self):
        self.script.event_publishers.setdefault(self, 0)
        self.script.event_publishers[self] += 1

    def unregister_publisher(self, *args):
        self.script.event_publishers.setdefault(self, 1)
        self.script.event_publishers[self] -= 1

    def create_publisher_task(self, coro: Coroutine) -> asyncio.Task:
        """Spawn a task from a coro, registering it as an event publisher and unregistering on completion"""
        self.register_publisher()
        task = asyncio.create_task(coro)
        task.add_done_callback(self.unregister_publisher)
        return task


class TimerScriptExtender(ScriptExtender):
    def __init__(self):
        super().__init__()
        self._timer_task: Optional[asyncio.Task] = None

    def extend_script(self, script: BaseLSLScript):
        super().extend_script(script)
        self.script.builtin_funcs["llSetTimerEvent"] = self._set_timer_event

    def _set_timer_event(self, seconds: float):
        if self._timer_task and not self._timer_task.done():
            # Should implicitly remove any event publisher registration
            self._timer_task.cancel()

        self._timer_task = None

        if seconds:
            # Have the timer tick in the background
            self._timer_task = self.create_publisher_task(self._tick_every(seconds))

    async def _tick_every(self, seconds: float):
        # Stupid hack to make this stop ticking when the state changes.
        # Maybe need hooks for state changes.
        start_state = self.script.current_state
        while True:
            await asyncio.sleep(seconds)
            # State changed while we were waiting, don't tick!
            if start_state != self.script.current_state:
                self._timer_task = None
                return

            # Only queue a timer event if one wasn't already pending
            if all(x[0] != "timer" for x in self.script.event_queue):
                # queue one up
                self.script.queue_event("timer", ())


class DateTimeScriptExtender(ScriptExtender):
    def __init__(self):
        super().__init__()
        self.start_time = 0.0

    def extend_script(self, script: BaseLSLScript):
        super().extend_script(script)
        self.start_time = time.time()
        self.script.builtin_funcs['llResetTime'] = self._reset_time
        self.script.builtin_funcs['llGetTime'] = lambda: time.time() - self.start_time
        self.script.builtin_funcs['llGetAndResetTime'] = self._get_and_reset_time
        self.script.builtin_funcs['llGetUnixTime'] = lambda: int(time.time())

    def _reset_time(self):
        self.start_time = time.time()

    def _get_and_reset_time(self):
        val = time.time() - self.start_time
        self._reset_time()
        return val
